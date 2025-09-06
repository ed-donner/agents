# %%
from openai import OpenAI
import os
from dotenv import load_dotenv
load_dotenv(override=True)

import json

# %%
pushover_user = os.getenv("PUSHOVER_USER")
pushover_token = os.getenv("PUSHOVER_TOKEN")
pushover_url = "https://api.pushover.net/1/messages.json"

def push(message):
    print(message)

# %%
def record_user_details(email, name="Name not provided", notes="not provided"):
    push(f"Recording interest from {name} with email {email} and notes {notes}")
    return {"recorded": "ok"}

record_user_details_json = {
    "name": "record_user_details",
    "description": "Use this tool to record that a user is interested in being in touch and provided an email address",
    "parameters": {
        "type":"object",
        "properties":{
            "email":{
                "type":"string",
                "description":"The email address of this user"
            },
            "name":{
                "type":"string",
                "description":"The user's name, if they provided it"
            },
            "nodes":{
                "type":"string",
                "description":"Any additional information about the conversation that's worth recording to give context"
            }
        },
        "required":["email"],
        "additionalProperties": False
    }
}

# %%
def record_unknown_question(question):
    push(f"Recording {question} asked that I couldn't answer")
    return {"recorded":"ok"}

record_unknown_question_json = {
    "name": "record_unknown_question",
    "description":"Always use this tool to record any question that couldn't be answered as you didn't know the answer",
    "parameters":{
        "type":"object",
        "properties":{
            "question":{
                "type":"string",
                "description":"The question that couldn't be answered"
            }
        },
        "required":["question"],
        "additionalProperties": False
    }
}

# %%
tools = [
    {"type":"function", "function":record_user_details_json},
    {"type":"function", "function":record_unknown_question_json}
]

# %%
def handle_tool_calls(tool_calls):
    results = []
    for tool_call in tool_calls:
        tool_name = tool_call.function.name
        arguments = json.loads(tool_call.function.arguments)
        print(f"tool called {tool_name}", flush=True)
        tool = globals().get(tool_name)
        result = tool(**arguments) if tool else {}
        results.append({"role":"tool", "content":json.dumps(result),"tool_call_id":tool_call.id})

        return results



# %%
from pypdf import PdfReader

linkedin = ''
linkedin_profile = PdfReader('me/Profile.pdf')
for page in linkedin_profile.pages:
    text = page.extract_text()
    if text:
        linkedin += text


# %%

name = 'Jongkook Kim'

from pydantic import BaseModel

class Evaluation(BaseModel):
    is_acceptable: bool
    feedback: str
    avator_response: str 

# %%
avator_system_prompt = f"""You are acting as {name}. You are answering questions on {name}'s website, 
particularly questions related to {name}'s career, background, skills and experience. 
Your responsibility is to represent {name} for interactions on the website as faithfully as possible. 
You are given a Resume of {name}'s background which you can use to answer questions. 
Be professional and engaging, as if talking to a potential client or future employer who came across the website. 
If you don't know the answer, say so.
If you don't know the answer to any question, use your record_unknown_question tool to record the question that you couldn't answer, even if it's about something trivial or unrelated to career. \
If the user is engaging in discussion, try to steer them towards getting in touch via email; ask for their email and record it using your record_user_details tool. """


def avator(message, history, evaluation: Evaluation):
    system_prompt = avator_system_prompt
    system_prompt += f"\n\n## Resume:\n{linkedin}\n\n"
    system_prompt += f"With this context, please chat with the user, always staying in character as {name}."


    if evaluation and not evaluation.is_acceptable:
        print(f"{evaluation.avator_response} is not acceptable. Retry")
        system_prompt += "\n\n## Previous answer rejected\nYou just tried to reply, but the quality control rejected your reply\n"
        system_prompt += f"## Your attempted answer:\n{evaluation.avator_response}\n\n"
        system_prompt += f"## Reason for rejection:\n{evaluation.feedback}\n\n"  

    messages = [{"role":"system", "content": system_prompt}] + history + [{"role":"user", "content": message}] 

    done = False
    while not done:
        llm_client = OpenAI().chat.completions.create(model="gpt-4o-mini", messages=messages, tools=tools)
        print('get response from llm')
        finish_reason = llm_client.choices[0].finish_reason
        if finish_reason == "tool_calls":
            print('this is tool calls')
            llm_response = llm_client.choices[0].message
            tool_calls = llm_response.tool_calls
            tool_response = handle_tool_calls(tool_calls)
            messages.append(llm_response)
            messages.extend(tool_response)
        else:
            print('this is message response')
            done = True

    return llm_client.choices[0].message.content

# %%
evaluator_system_prompt = f"You are an evaluator that decides whether a response to a question is acceptable. \
You are provided with a conversation between a User and an Agent. Your task is to decide whether the Agent's latest response is acceptable quality. \
The Agent is playing the role of {name} and is representing {name} on their website. \
The Agent has been instructed to be professional and engaging, as if talking to a potential client or future employer who came across the website. \
The Agent has been provided with context on {name} in the form of their Resume details. Here's the information:"

def evaluator_user_prompt(question, avator_response, history):
    user_prompt = f"Here's the conversation between the User and the Agent: \n\n{history}\n\n"
    user_prompt += f"Here's the latest message from the User: \n\n{question}\n\n"
    user_prompt += f"Here's the latest response from the Agent: \n\n{avator_response}\n\n"
    user_prompt += "Please evaluate the response, replying with whether it is acceptable and your feedback."
    return user_prompt

def evaluator(question, avator_response, history) -> Evaluation:
    system_prompt = evaluator_system_prompt + f"## Resume:\n{linkedin}\n\n"
    system_prompt += f"With this context, please evaluate the latest response, replying with whether the response is acceptable and your feedback."

    messages = [{"role":"system", "content":system_prompt}] + [{"role":"user", "content":evaluator_user_prompt(question, avator_response, history)}]
    llm_client = OpenAI(api_key=os.getenv('GOOGLE_API_KEY'), base_url='https://generativelanguage.googleapis.com/v1beta/openai/')
    evaluation = llm_client.beta.chat.completions.parse(
        model="gemini-2.0-flash",
        messages=messages,
        response_format=Evaluation
    )

    evaluation = evaluation.choices[0].message.parsed
    evaluation.avator_response = avator_response
    return evaluation

# %%
max_attempt = 2

def orchestrator(message, history):
    avator_response = avator(message, history, None)
    print('get response from avator')

    for attempt in range(1, max_attempt + 1):
        print(f'try {attempt} times')

        evaluation = evaluator(message, avator_response, history)
        print('get response from evaluation')

        if not evaluation.is_acceptable:
            print('reponse from avator is not acceptable')
            message_with_feedback = evaluation.feedback + message
            avator_response = avator(message_with_feedback, history, evaluation)
        else:
            print('response from avator is acceptable')
            break

    return avator_response

# %%
import gradio
gradio.ChatInterface(orchestrator, type="messages").launch()


