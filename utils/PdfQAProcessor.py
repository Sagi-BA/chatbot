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
        print(filename)
        with open(filename, 'rb') as f:
            embeddings, chunks = pickle.load(f)
        return embeddings, chunks

    # Cosine similarity function to compare embeddings
    def cosine_similarity(self, vec1, vec2):
        return np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))

    # Find the most relevant chunk based on the question
    def get_relevant_chunk(self, question, embeddings, chunks):
        question_embedding = self.create_embedding(question)
        similarities = [self.cosine_similarity(question_embedding, emb) for emb in embeddings]
        most_relevant_chunk = chunks[np.argmax(similarities)]
        return most_relevant_chunk

    def generate_answer(self, question, context, system_prompt):
        print(question)
        response = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "system", "content": f"Context: {context}"},
                {"role": "user", "content": question}
            ],
            max_tokens=850
        )
        
        return response.choices[0].message.content.strip()

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
        relevant_chunk = self.get_relevant_chunk(question, embeddings, chunks)

        # Generate and return the answer, now with the system prompt
        answer = self.generate_answer(question, relevant_chunk, system_prompt)

        return answer

# Example usage
if __name__ == "__main__":
    # Initialize the processor
    processor = PdfQAProcessor()

    # Path to your Hebrew PDF
    pdf_name = "pool.pdf"
    
    # Example question
    question = "מהם הזמני פתיחה?"
    question = "האם יש מנוי שנתי? אם כן מה זה כולל ?"

     # Define your system prompt
    system_prompt = (
        "אתה מומחה בניהול בריכות ומומחה בתחום. עליך לענות על שאלות בנוגע לבריכה, כולל זמני פתיחה, מחירים, וחוגים."        
    )

    # Get the answer from the PDF
    answer = processor.process_pdf_and_answer(pdf_name, question, system_prompt)

    print(f"Answer: {answer}")

