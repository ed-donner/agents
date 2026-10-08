import os
import requests
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())

def get_data():
    api_key = os.environ.get("OPENROUTER_API_KEY")
    url = f"https://api.example.com/data?key={api_key}"
    response = requests.get(url)
    return response.json()

def execute_user_code(user_input):
    # INSECURE: using eval on user input
    return eval(user_input)

if __name__ == "__main__":
    print(get_data())
