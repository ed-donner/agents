import os
from dotenv import load_dotenv
from IPython.display import Markdown, display
from openai import OpenAI
load_dotenv(override=True)

openai_api_key = os.getenv('OPENAI_API_KEY')
gemini_api_key = os.getenv('GEMINI_API_KEY')
print("GEMINI_API_KEY:", bool(os.getenv('GEMINI_API_KEY')))

if openai_api_key:
    print(f"OpenAI API Key exists and begins {openai_api_key[:8]}")
else:
    print("OpenAI API Key not set - please head to the troubleshooting guide in the setup folder")

if gemini_api_key:
    print(f"Gemini API Key exists and begins {gemini_api_key[:2]}")
else:
    print("Gemini API Key not set - please head to the troubleshooting guide in the setup folder")
    
openai = OpenAI()

# request = "come up with an online business idea that can be executed entierly with AI and would be very profitable,"
# request += "i want to ask other LLMs to come up with a detailed plan for this business idea so i can determine which LLM is best suited to help me execute this business idea"
# request += " provide the business idea in a single sentence"
request="i want to create and sell source code online using AI, come up with a specific business idea for this"
messages = [{"role": "user", "content": request}]
response = openai.chat.completions.create(
    model="gpt-4.1-nano",
    messages=messages,
)
idea = response.choices[0].message.content
print("Business Idea:", idea)
competitors = ["gpt-4.1-mini"]
#"Gemini 3 Flash (Preview)","Gemini 2.5 Flash-Lite","Gemini 2.5 Flash"
answers = []
messages = [{"role": "user", "content": f"Provide a detailed plan to execute the following business idea: {idea} inclusive of steps to take, tools to use and marketing strategies, expected revenue duration on cost "}]
for competitor in competitors:
    response = openai.chat.completions.create(
        model=competitor,
        messages=messages,
    )
    answers.append((competitor, response.choices[0].message.content))   
for answer in answers:
    print(f"## Response from {answer[0]}\n\n{answer[1]}")