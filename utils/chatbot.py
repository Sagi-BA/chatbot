import os
from groq import Groq
from dotenv import load_dotenv


# Load environment variables
load_dotenv()

groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def get_prompt(system_prompt, user_prompt):
    try:
        response = groq_client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            model=os.getenv("GROQ_MODEL", "llama3-70b-8192"),
            temperature=0.0,
            max_tokens=int(os.getenv("GROQ_MAX_TOKENS", 1024)),
            stream=False,
        )
        new_prompt = response.choices[0].message.content
        return new_prompt
    except Exception as e:
        print(f"Error in get_prompt: {str(e)}")
        return f"אני מצטער, אך אירעה שגיאה בעת עיבוד השאלה שלך. האם תוכל לנסח אותה מחדש?"
