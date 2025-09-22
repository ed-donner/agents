from dotenv import load_dotenv
from openai import OpenAI
import json
import os
import requests
from pypdf import PdfReader
import gradio as gr
import pprint


load_dotenv(override=True)

openai = OpenAI()

pushover_user = os.getenv("PUSHOVER_USER")
pushover_token = os.getenv("PUSHOVER_TOKEN")
pushover_url = "https://api.pushover.net/1/messages.json"

if pushover_user:
    print(f"Pushover user found and starts with {pushover_user[0]}")
else:
    print("Pushover user not found")

if pushover_token:
    print(f"Pushover token found and starts with {pushover_token[0]}")
else:
    print("Pushover token not found")


def push(message):
  print(f"Push: {message}")
  payload = {"user": pushover_user, "token": pushover_token, "message": message}
  requests.post(pushover_url, data=payload)


def record_user_details(email, name="Name not provided", notes="not provided"):
    push(f"Recording interest from {name} with email {email} and notes {notes}")
    return {"recorded": "ok"}


def record_unknown_question(question):
    push(f"Recording {question} asked that I couldn't answer")
    answerObj = search_common_questions(question)
    return {"recorded": "ok", "answer": answerObj["answer"], "found": answerObj["found"]}


import os
import psycopg2

def search_common_questions(question):
    # print("Searching AI-matched answer for:", question)
    return ai_match_qa(question)



def fetch_all_qa():
    try:
        conn = psycopg2.connect(
            host=os.getenv('DB_HOST'),
            port=os.getenv('DB_PORT', '5432'),
            database=os.getenv('DB_NAME'),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD')
        )
        cursor = conn.cursor()
        cursor.execute("SELECT question, answer FROM qa")
        rows = cursor.fetchall()
        conn.close()
        return [{"question": q, "answer": a} for q, a in rows]
    except Exception as e:
        print(f"Database connection failed: {e}")
        return []
    
def ai_match_qa(user_question):
    qa_pairs = fetch_all_qa()
    if not qa_pairs:
        return {"answer": "Sorry, there was a technical issue accessing the Q&A database.", "found": False}

    # Prepare context for AI
    context = "\n".join([f"Q: {qa['question']}\nA: {qa['answer']}" for qa in qa_pairs])

    prompt = f"""
    You are given a list of questions and answers. A user asked the following question:
    "{user_question}"

    Find the best matching question in the list above and give the corresponding answer.
    If you cannot find a relevant answer, say you don't know.
    List of Q&A:
    {context}
    """

    response = openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}]
    )
    answer = response.choices[0].message.content.strip()
    found = not any(phrase in answer.lower() for phrase in ["i don't know", "sorry", "no answer"])

    return {"answer": answer, "found" : found}


record_user_details_json = {
    "name": "record_user_details",
    "description": "Use this tool to record that a user is interested in being in touch and provided an email address",
    "parameters": {
        "type": "object",
        "properties": {
            "email": {
                "type": "string",
                "description": "The email address of this user"
            },
            "name": {
                "type": "string",
                "description": "The user's name, if they provided it"
            }
            ,
            "notes": {
                "type": "string",
                "description": "Any additional information about the conversation that's worth recording to give context"
            }
        },
        "required": ["email"],
        "additionalProperties": False
    }
}


record_unknown_question_json = {
    "name": "record_unknown_question",
    "description": "Always use this tool to record any question that couldn't be answered as you didn't know the answer",
    "parameters": {
        "type": "object",
        "properties": {
            "question": {
                "type": "string",
                "description": "The question that couldn't be answered"
            },
        },
        "required": ["question"],
        "additionalProperties": False
    }
}

search_common_questions_json = {
    "name": "search_common_questions",
    "description": "Search the common Q&A database to answer frequently asked questions about Harsh Bhama.",
    "parameters": {
        "type": "object",
        "properties": {
            "question": {
                "type": "string",
                "description": "The question asked by the user"
            }
        },
        "required": ["question"],
        "additionalProperties": False
    }
}


tools = [{"type": "function", "function": record_user_details_json},
        {"type": "function", "function": record_unknown_question_json},
        {"type": "function", "function": search_common_questions_json}]




def handle_tool_calls(tool_calls):
    results = []
    for tool_call in tool_calls:
        tool_name = tool_call.function.name
        arguments = json.loads(tool_call.function.arguments)
     

        # THE BIG IF STATEMENT!!!

        if tool_name == "record_user_details":
            result = record_user_details(**arguments)
        elif tool_name == "record_unknown_question":
            result = record_unknown_question(**arguments)
            results.append({"role": "tool","content": json.dumps(result),"tool_call_id": tool_call.id, "resultFromDb": result["found"], "answerFromDb": result["answer"]})
        

    return results


reader = PdfReader("Profile.pdf")
linkedin = ""
for page in reader.pages:
    text = page.extract_text()
    if text:
        linkedin += text 

readerResume = PdfReader("resume.pdf")

for page in readerResume.pages:
    text = page.extract_text()
    if text:
        linkedin += text 

name = "Harsh Bhama"

system_prompt = f"You are acting as {name}. You are answering questions on {name}'s website, \
particularly questions related to {name}'s career, background, skills and experience. \
Your responsibility is to represent {name} for interactions on the website as faithfully as possible. \
You are given a resume and linkedin profile of {name}'s which you can use to answer questions. \
Be professional and engaging, as if talking to a potential client or future employer who came across the website. \
If you don't know the answer to any question, use your record_unknown_question tool to record the question that you couldn't answer, even if it's about something trivial or unrelated to career. \
If the user is engaging in discussion, try to steer them towards getting in touch via email; ask for their email and record it using your record_user_details tool. "

system_prompt += f"LinkedIn Profile and Harsh's resume:\n{linkedin}\n\n"
system_prompt += f"With this context, please chat with the user, always staying in character as {name}."
    



def chat(message, history):
    messages = [{"role": "system", "content": system_prompt}] + history + [{"role": "user", "content": message}]
    done = False
    while not done:
        # LLM call
        response = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            tools=tools
        )

        finish_reason = response.choices[0].finish_reason
        # print(f"Finish reason: {finish_reason}", flush=True)

        message_obj = response.choices[0].message

        if finish_reason == "tool_calls":
            tool_calls = message_obj.tool_calls
            results = handle_tool_calls(tool_calls)

            # Append tool call message AND tool results
            messages.append(message_obj)
            messages.extend(results)
            if results[results.__len__() - 1].get("resultFromDb") == True:
                done = True
                final_reply = results[results.__len__() - 1].get("answerFromDb")

        else:
            # LLM has finished generating a proper answer
            done = True
            final_reply = message_obj.content

    return final_reply




from pydantic import BaseModel

class Evaluation(BaseModel):
    is_acceptable: bool
    feedback: str

evaluator_system_prompt = """You are an evaluator that decides whether a response to a question is acceptable. You are provided with a conversation between a User and an Agent. Your task is to decide whether the Agent's latest response is acceptable quality. The Agent is playing the role of Ed Donner and is representing Ed Donner on their website. The Agent has been instructed to be professional and engaging, as if talking to a potential client or future employer who came across the website. The Agent has been provided with context on Harsh Bhama in the form of their resume and LinkedIn details. Here's the information:
## LinkedIn Profile and Resume:
{linkedin} """
evaluator_system_prompt += f"\n\n## Conversation:\n{{conversation}}\n\n"


def evaluator_user_prompt(reply, message, history):
    user_prompt = f"Here's the conversation between the User and the Agent: \n\n{history}\n\n"
    user_prompt += f"Here's the latest message from the User: \n\n{message}\n\n"
    user_prompt += f"Here's the latest response from the Agent: \n\n{reply}\n\n"
    user_prompt += "Please evaluate the response, replying with whether it is acceptable and your feedback."
    return user_prompt


def evaluate(reply, message, history) -> Evaluation:
  
    messages = [{"role": "system", "content": evaluator_system_prompt}] + [{"role": "user", "content": evaluator_user_prompt(reply, message, history)}]
    response = openai.beta.chat.completions.parse(model="o4-mini", messages=messages, response_format=Evaluation)
    return response.choices[0].message.parsed



def rerun(reply, message, history, feedback):
    updated_system_prompt = system_prompt + "\n\n## Previous answer rejected\nYou just tried to reply, but the quality control rejected your reply\n"
    updated_system_prompt += f"## Your attempted answer:\n{reply}\n\n"
    updated_system_prompt += f"## Reason for rejection:\n{feedback}\n\n"
    messages = [{"role": "system", "content": updated_system_prompt}] + history + [{"role": "user", "content": message}]
    response = openai.chat.completions.create(model="gpt-4o-mini", messages=messages)
    return response.choices[0].message.content




def chatN(message, history):
    if "patent" in message:
        system = system_prompt + "\n\nEverything in your reply needs to be in pig latin - \
              it is mandatory that you respond only and entirely in pig latin"
    else:
        system = system_prompt
    messages = [{"role": "system", "content": system}] + history + [{"role": "user", "content": message}]
    response = openai.chat.completions.create(model="gpt-4o-mini", messages=messages)
    reply =response.choices[0].message.content

    evaluation = evaluate(reply, message, history)
    
    if evaluation.is_acceptable:
        print("Passed evaluation - returning reply")
    else:
        print("Failed evaluation - retrying")
        print(evaluation.feedback)
        reply = rerun(reply, message, history, evaluation.feedback)       
    return reply

gr.ChatInterface(chat, type="messages").launch()