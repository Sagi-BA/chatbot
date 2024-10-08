import fitz  # PyMuPDF
import openai
import numpy as np
import os
import pickle
from dotenv import load_dotenv
from groq import Groq
from collections import deque

class PdfQAProcessor:
    def __init__(self, data_folder="data", embeddings_folder="embeddings"):
        # Load environment variables from the .env file
        load_dotenv()

        # Get the API key from the environment variable
        self.model_type = os.environ.get("MODEL_TYPE")
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.embeddings_model = os.getenv("EMBEDDINGS_MODEL") #"text-embedding-ada-002", #text-embedding-3-small or any other embedding model
        self.llm_model = os.getenv("LLM_MODEL", "llama3-70b-8192") #"gpt-4o", #"gpt-4o",  "gpt-4o-mini"# Use GPT-4 or a smaller model if desired sagi
        self.max_token = int(os.getenv("MAX_TOKENS", 1024))
        # Check if the API key exists, raise an error if not found
        if not self.api_key:
            raise ValueError("OpenAI API key not found. Please add 'OPENAI_API_KEY' to your .env file.")

        # Set the OpenAI API key
        openai.api_key = self.api_key

        # Set the folders for PDFs and embeddings
        self.data_folder = data_folder
        self.embeddings_folder = embeddings_folder

        # Ensure the embeddings folder exists
        os.makedirs(self.embeddings_folder, exist_ok=True)

        # Initialize conversation history
        self.conversation_history = deque(maxlen=10)

    # Extract text from PDF using PyMuPDF
    def extract_text_from_pdf(self, pdf_name):
        pdf_path = os.path.join(self.data_folder, pdf_name)
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF file '{pdf_name}' not found in '{self.data_folder}'")

        pdf_document = fitz.open(pdf_path)
        text = ""
        for page_num in range(len(pdf_document)):
            page = pdf_document.load_page(page_num)
            text += page.get_text("text")
        return text

    # Create embedding using OpenAI's API
    def create_embedding(self, text):
        
        response = openai.embeddings.create(
            model= self.embeddings_model,
            input=text
        )

        # Access the embeddings from the response
        embedding = response.data[0].embedding
        return embedding

    # Save embeddings to a file (Pickle)
    def save_embeddings_to_file(self, embeddings, chunks, filename):
        with open(filename, 'wb') as f:
            pickle.dump((embeddings, chunks), f)

    # Load embeddings from a file (Pickle)
    def load_embeddings_from_file(self, filename):
        # print(filename)
        with open(filename, 'rb') as f:
            embeddings, chunks = pickle.load(f)
         
        return embeddings, chunks

    # Cosine similarity function to compare embeddings
    def cosine_similarity(self, vec1, vec2):
        return np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))

    # Find the most relevant chunk based on the question
    def get_top_relevant_chunks(self, question, embeddings, chunks, top_n=3):
        """
        Retrieves the top-n most relevant chunks based on cosine similarity.
        
        Parameters:
        - question: The input query string.
        - embeddings: A list of embeddings corresponding to the chunks.
        - chunks: The actual chunks of text.
        - top_n: Number of top relevant chunks to retrieve (default is 3).
        
        Returns:
        - A single string containing the top-n most relevant chunks concatenated.
        """
        
        # Create the embedding for the question
        question_embedding = self.create_embedding(question)
        
        # Compute cosine similarities between the question and the chunks
        similarities = [self.cosine_similarity(question_embedding, emb) for emb in embeddings]
        
        # Get indices of top-n most relevant chunks
        top_indices = np.argsort(similarities)[-top_n:]  # Get top-n largest similarity scores
        
        # Retrieve the top-n most relevant chunks and concatenate them
        top_relevant_chunks = [chunks[i] for i in top_indices]
        
        # Return concatenated chunks as context
        return "\n\n".join(top_relevant_chunks)

    def generate_answer(self, question, context, system_prompt):
        """
        Generates an answer in Hebrew using the provided context and system prompt with GPT-4.
        If no relevant context is found or there's no response from GPT-4, it notifies the user that no relevant information is available.
        
        Parameters:
        - question: The user's question in Hebrew.
        - context: The relevant chunks (context) in Hebrew to guide the answer. Can be an empty string if no relevant chunks were found.
        - system_prompt: Instructions for how the assistant should behave (can also be in Hebrew).
        
        Returns:
        - Generated answer in Hebrew from GPT-4o, or a message indicating no relevant information or an error occurred.
        """
        
        # Check if the context is empty or too short
        if not context or len(context.strip()) == 0:
            return "לא נמצא מידע רלוונטי לשאלה שלך. נסה לשאול שאלה אחרת או לפרט יותר."
        
        try:
            # Prepare the conversation history
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "assistant", "content": f"Context: {context}"},
            ]
            
            # Add conversation history
            for history_item in self.conversation_history:
                messages.append({"role": "user", "content": history_item["question"]})
                messages.append({"role": "assistant", "content": history_item["answer"]})
            
            # Add the current question
            messages.append({"role": "user", "content": question})
            
            if self.model_type == "chatgpt":
                response = openai.chat.completions.create(
                    model= self.llm_model, #"gpt-4o", #"gpt-4o",  "gpt-4o-mini"# Use GPT-4 or a smaller model if desired sagi
                    messages=messages,
                    max_tokens = self.max_token,  # Adjust based on the answer length you expect
                    temperature=0.0  # Low temperature for more deterministic responses
                )
                answer = response.choices[0].message.content.strip()

            elif self.model_type == "qroq":
                groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))
                response = groq_client.chat.completions.create(
                    messages=messages,
                    model=self.llm_model,
                    temperature=0.0,
                    max_tokens=self.max_token,
                    stream=False
                )
                answer = response.choices[0].message.content.strip()

            # Check if the answer is empty
            if not answer:
                return "לא הצלחתי למצוא תשובה לשאלה שלך בהתבסס על המידע הקיים. נסה לשאול שאלה אחרת."
            
            # Update conversation history
            self.conversation_history.append({"question": question, "answer": answer})

            return answer
        
        except Exception as e:
            # Handle errors like network issues, API errors, etc.
            print(f"Error occurred: {e}")
            return "אירעה שגיאה בעת יצירת תשובה. אנא נסה שוב מאוחר יותר."

    # Process the PDF, store embeddings, and answer questions
    def process_pdf_and_answer(self, pdf_name, question, system_prompt):
        # Remove the ".pdf" extension and prepare the save path for embeddings
        file_base_name = os.path.splitext(pdf_name)[0]
        save_path = os.path.join(self.embeddings_folder, f"{file_base_name}_embeddings.pkl")        

        # Check if embeddings already exist in file
        if os.path.exists(save_path):
            print(f"Loading precomputed embeddings from {save_path}...")
            embeddings, chunks = self.load_embeddings_from_file(save_path)
            
        else:
            print(f"Processing and embedding PDF: {pdf_name}...")
            # Extract text from the PDF
            pdf_text = self.extract_text_from_pdf(pdf_name)

            # Split the PDF text into chunks (if necessary)
            chunks = [pdf_text[i:i + 2000] for i in range(0, len(pdf_text), 2000)]

            # Generate embeddings for each chunk
            embeddings = [self.create_embedding(chunk) for chunk in chunks]

            # Save embeddings to file for future use
            self.save_embeddings_to_file(embeddings, chunks, save_path)

        # Get the most relevant chunk for the question
        relevant_chunk = self.get_top_relevant_chunks(question, embeddings, chunks, top_n=3)

        # Generate and return the answer, now with the system prompt and conversation history
        answer = self.generate_answer(question, relevant_chunk, system_prompt)

        return answer

    def clear_conversation_history(self):
        self.conversation_history.clear()

# Example usage
if __name__ == "__main__":
    # Initialize the processor
    processor = PdfQAProcessor()

    # System prompt (can be in Hebrew as well)
    system_prompt = """
    אתה עוזר חכם שתמיד מתנהג כמו נציג שירות מקצועי, אמפתי ומבין. 
    עליך לספק תשובות ברורות, מדויקות ומכבדות, תוך גילוי הבנה והכלה לצרכי המשתמש. 
    בכל תשובה שלך, הקפד להיות תומך וסבלני, גם כאשר אין לך את כל המידע הנדרש. 
    אם לא נמצא מידע רלוונטי לשאלה המבוסס על ההקשר שסופק, עליך להחזיר את ההודעה הבאה: 
    'לא הצלחתי למצוא תשובה לשאלה שלך בהתבסס על המידע הקיים. נסה לשאול שאלה אחרת.'
    ספק תשובות מבוססות על ההקשר שסופק בלבד, תוך שמירה על מקצועיות ושירותיות.
    """

    # Path to your Hebrew PDF
    pdf_name = "general_info.pdf"
    
    # Example question
    question = "מי זה עמית ברק?"
    # question = "האם יש מנוי שנתי? אם כן מה זה כולל ?"

     # Define your system prompt
    # system_prompt = (
    #     "אתה מומחה בניהול בריכות ומומחה בתחום. עליך לענות על שאלות ששואלים אותך. התשובות שלך הם רק מהתוכן שאתה מקבל ולא משום מקום אחר! אם אין לך תשובה אז אתה עונה: סליחה, אין לי את המידע הזה."        
    # )    

    # Get the answer from the PDF
    answer = processor.process_pdf_and_answer(pdf_name, question, system_prompt)
    print(f"Answer: {answer}")

    question = "מה הטלפון שלו?"
     # Get the answer from the PDF
    answer = processor.process_pdf_and_answer(pdf_name, question, system_prompt)

    print(f"Answer: {answer}")