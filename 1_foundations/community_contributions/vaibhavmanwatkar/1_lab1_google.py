from dotenv import load_dotenv
load_dotenv(override=True)

import os
import google.generativeai as genai  # pyright: ignore[reportMissingImports]

genai.configure(api_key=os.getenv('GOOGLE_API_KEY'))
model = genai.GenerativeModel(model_name="gemini-2.0-flash-exp")

response = model.generate_content(["What is 2+2?"])
print(response.text)