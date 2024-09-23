import fitz  # PyMuPDF
import openai
import numpy as np
import os
import pickle
from dotenv import load_dotenv

class PdfQAProcessor:
    def __init__(self, data_folder="data", embeddings_folder="embeddings"):
        # Load environment variables from the .env file
        load_dotenv()

        # Get the API key from the environment variable
        self.api_key = os.getenv("OPENAI_API_KEY")

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
            model="text-embedding-ada-002",  # or any other embedding model
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
            # Call OpenAI's GPT-4 to generate the answer
            # Otherwise, proceed to generate the answer using the context
            response = openai.chat.completions.create(
                model="gpt-4o-mini", #"gpt-4o",  # Use GPT-4 or a smaller model if desired
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "assistant", "content": f"Context: {context}"},  # Providing the context
                    {"role": "user", "content": question}  # User's query
                ],
                max_tokens=850,  # Adjust based on the answer length you expect
                temperature=0.0  # Low temperature for more deterministic responses
            )
            
            # Extract and return the response from the assistant
            answer = response.choices[0].message.content.strip()

            # Check if the answer is empty
            if not answer:
                return "לא הצלחתי למצוא תשובה לשאלה שלך בהתבסס על המידע הקיים. נסה לשאול שאלה אחרת."
            
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

        # Generate and return the answer, now with the system prompt
        answer = self.generate_answer(question, relevant_chunk, system_prompt)

        return answer

# Example usage
if __name__ == "__main__":
    # Initialize the processor
    processor = PdfQAProcessor()

    # Path to your Hebrew PDF
    pdf_name = "general_info.pdf"
    
    # Example question
    question = "מה הטלפון של עמית ברק?"
    # question = "האם יש מנוי שנתי? אם כן מה זה כולל ?"

     # Define your system prompt
    # system_prompt = (
    #     "אתה מומחה בניהול בריכות ומומחה בתחום. עליך לענות על שאלות ששואלים אותך. התשובות שלך הם רק מהתוכן שאתה מקבל ולא משום מקום אחר! אם אין לך תשובה אז אתה עונה: סליחה, אין לי את המידע הזה."        
    # )

    # System prompt (can be in Hebrew as well)
    system_prompt = """
    אתה עוזר חכם שתמיד מתנהג כמו נציג שירות מקצועי, אמפתי ומבין. 
    עליך לספק תשובות ברורות, מדויקות ומכבדות, תוך גילוי הבנה והכלה לצרכי המשתמש. 
    בכל תשובה שלך, הקפד להיות תומך וסבלני, גם כאשר אין לך את כל המידע הנדרש. 
    אם לא נמצא מידע רלוונטי לשאלה המבוסס על ההקשר שסופק, עליך להחזיר את ההודעה הבאה: 
    'לא הצלחתי למצוא תשובה לשאלה שלך בהתבסס על המידע הקיים. נסה לשאול שאלה אחרת.'
    ספק תשובות מבוססות על ההקשר שסופק בלבד, תוך שמירה על מקצועיות ושירותיות.
    """

    # Get the answer from the PDF
    answer = processor.process_pdf_and_answer(pdf_name, question, system_prompt)

    print(f"Answer: {answer}")

