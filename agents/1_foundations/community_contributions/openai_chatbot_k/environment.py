from dotenv import load_dotenv
import os

load_dotenv(override=True)


pushover_user = os.getenv('PUSHOVER_USER')
pushover_token = os.getenv('PUSHOVER_TOKEN')
api_key = os.getenv("OPENAI_API_KEY")
ratelimit_api = os.getenv("RATELIMIT_API")
request_token = os.getenv("REQUEST_TOKEN")

ai_model = "gpt-4o-mini"
resume_file = "./me/software-developer.pdf"
summary_file = "./me/summary.txt"

name = "Kenneth Andales"
