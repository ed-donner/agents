import os 
from dotenv import load_dotenv
load_dotenv()


RESEND_API_KEY = os.getenv("RESEND_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
USER_NAME = os.getenv("USER_NAME")