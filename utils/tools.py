import os
from io import BytesIO
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def save_uploaded_file(uploaded_file, upload_dir="uploads", filename=None):
    """
    Save the uploaded file to the specified directory and return the file path.
    """
    if not os.path.exists(upload_dir):
        os.makedirs(upload_dir)
    
    if filename is None:
        filename = uploaded_file.name

    file_path = os.path.join(upload_dir, filename)
    
    if isinstance(uploaded_file, BytesIO):
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getvalue())
    else:
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
    
    return file_path

def get_image_url(query):
    UNSPLASH_ACCESS_KEY = os.getenv("UNSPLASH_ACCESS_KEY")

    url = f"https://api.unsplash.com/search/photos?query={query}&client_id={UNSPLASH_ACCESS_KEY}"
    response = requests.get(url)
    data = response.json()
    if data['results']:
        return data['results'][0]['urls']['regular']
    return None

if __name__ == "__main__":
    image_url = get_image_url("Mountain")
    print(image_url)