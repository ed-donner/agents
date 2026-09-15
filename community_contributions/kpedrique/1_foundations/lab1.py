import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv(override=True)

openai_api_key = os.getenv('OPENAI_API_KEY')

openai = OpenAI()
def calling_openai (model, messages):
  response = openai.chat.completions.create(model=model, messages=messages)
  return response.choices[0].message.content

if __name__ == "__main__":
  try:
    questions = [
      "Pick a business area that might be worth exploring for an Agentic AI opportunity",
      "Please, present a pain-point in that business, something challenging that might be ripe for an Agentic solution",
      "Pleaser, propose the Agentic AI solution."
    ]
    models = [
      "gpt-5.4-mini",
      "gpt-5.4-nano",
      "gpt-5.4"
    ]
    messages = [{"role": "system", "content": "You are a business expert and a visionary and expert usign agents"}]

    for index, question in enumerate(questions):
      messages.append({"role": "user", "content": question})
      print(f"""
      {models[index]} question:
      {question}
      """)
      content = calling_openai(models[index], messages)
      if content:
         messages.append({ "role": "user", "content": content })
         print(f"""
         {models[index]} response: 
         {content}
         """)
  except Exception as e:
    print("Exception -> ", e)