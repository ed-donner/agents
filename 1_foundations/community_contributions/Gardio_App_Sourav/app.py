from dotenv import load_dotenv
from openai import OpenAI
import json
import os
import requests
from pypdf import PdfReader
import gradio as gr
from pydantic import BaseModel

load_dotenv(override=True)


def push(text):
    requests.post(
        "https://api.pushover.net/1/messages.json",
        data={
            "token": os.getenv("PUSHOVER_TOKEN"),
            "user": os.getenv("PUSHOVER_USER"),
            "message": text,
        }
    )



def record_user_details(email, name="Name not provided", notes="Notes not provided"):
    push(f"Recording interest from {name} having email id {email} and notes : {notes}")
    return{"recorded" : "ok"}

def record_unknown_questions(question):
    push(f"Unknwon question{question} has been asked, which I can not answer")
    return{"recorded" : "ok"}

record_user_details_json = {
"name" : "record_user_details",
"description" : "Use this tool to record the user name and emial if that neing is interested in connecting",
"parameters" : {
    "type" : "object",
    "properties":{
        "email" : {
            "type" : "string",
            "description" : "The Users email id"
        },
        "name":{
            "type" : "string",
            "description" : "the name of the User, if they provide it"
        },
        "notes" :{
            "type" : "string",
            "descrioption" : "Any additonal information about the conversation that worth noting, for more context"
        }
    },
    "required" : ["email"],
    "additionalproperties" : False
    }
}

record_unknown_questions_json ={
    "name" : "record_unknown_questions",
    "description" : "Use this tool to capture any unknown question which you are unable to answer",
    "Parameters" : {
        "type" : "object",
        "properties" : {
            "question" :{
                "type" : "string",
                "description" : "The User asks the question which could't be answered"
            },
            "required" : ["question"],
            "additionalpropertise" : False
        }
    }
}

tools = [
    {"type" : "function", "function" : record_user_details_json},
    {"type" : "function", "function" : record_unknown_questions_json}
]



class Evaluation(BaseModel):
    is_acceptable: bool
    feedback: str

class Me :

    def __init__(self) :
        self.openai = OpenAI()
        self.trinity = OpenAI(api_key=os.getenv("OPENROUTER_API_KEY"), base_url="https://openrouter.ai/api/v1")
        self.name = "Sourav"
        reader = PdfReader("me/Sourav_Profile.pdf")
        self.linkdin = ""
        for page in reader.pages :
            text = page.extract_text()
            if text :
                self.linkdin += text

        with open("me/sourav_summary.txt","r", encoding="utf-8") as f:
            self.summary = f.read()




    def handle_tool_calls(self,tool_calls):
        results = []
        for tool_call in tool_calls:
            tool_name = tool_call.function.name
            arguments = json.loads(tool_call.function.arguments)
            print(f"Tool called : {tool_name}", flush=True)
            tool = globals.get(tool_name)
            result = tool(**arguments) if tool else {}
            results.append({"role" : "tool", "content" : json.dumps(result), "tool_call_id" : tool_call.id})
        return results



    def system_prompt(self) :
        system_prompt  = f"You are acting as {self.name}. You are answering questions on {self.name}'s website, \
                            particularly questions related to {self.name}'s career, background, skills and experience\
                            Your responsibility is to represent {self.name} for interactions on the website as faithfully as possible. \
                            You are given a summary of {self.name}'s background and LinkedIn profile which you can use to answer questions. \
                            Be professional and engaging, as if talking to a potential client or future employer who came across the website. \
                            If you don't know the answer to any question, use your record_unknown_question tool to record the question that you couldn't answer,\
                            even if it's about something trivial or unrelated to career. \
                            If the user is engaging in discussion, try to steer them towards getting in touch via email; ask for their email and record it using your record_user_details tool. "
        
        system_prompt += f"\n\n## Summary:\n{self.summary}\n\n## LinkedIn Profile:\n{self.linkdin}\n\n"
        system_prompt += f"With this context, please chat with the user, always staying in character as {self.name}."
        return system_prompt





    def evaluator_system_prompt(self):
        evaluator_system_prompt = f"You are an evaluator and Moderator that decides whether a response to a question is acceptable \
                                    You are provided with a conversation between a User and an Agent. Your task is to decide whether the Agent's \
                                    latest response is acceptable quality also You can suggest some improvements also  \
                                    You are the Manager who oversees the communications and PR for the {self.name} \
                                    The Agent is playing the role of {self.name} and is representing {self.name} on their website. \
                                    The Agent has been instructed to be professional and engaging, as if talking to a potential client or future employer who came across the website. \
                                    The Agent has been provided with context on {self.name} in the form of their summary and LinkedIn details. Here's the information:"

        evaluator_system_prompt += f"\n\n## Summary:\n{self.summary}\n\n## LinkedIn Profile:\n{self.linkdin}\n\n"
        evaluator_system_prompt += f"With this context, please evaluate the latest response, replying with whether the response is acceptable and your feedback."
        return evaluator_system_prompt

    def evaluator_user_prompt(self,reply, message,history):
        user_prompt = f"Here is the converstation between user and Agent: \n\n{history}\n\n"
        user_prompt += f"Here is the latest message from the user: \n\n{message}\n\n"
        user_prompt += f"Here is the latest reply from the Agent: \n\n{reply}\n\n"
        user_prompt += f"Please evaluate whether the response from Agent is acceptable or not"
        return user_prompt


    def evaluate(self,reply, message, history) -> Evaluation :
        messages = [{"role": "system", "content": self.evaluator_system_prompt()}] + [{"role": "user" , "content": self.evaluator_user_prompt(reply,message,history)}]
        response = self.trinity.beta.chat.completions.parse(model="arcee-ai/trinity-mini:free", messages=messages, response_format=Evaluation)
        return response.choices[0].message.parsed




    def rerun(self,reply, message, history, feedback):
        updated_system_prompt = self.system_prompt() + "\n\n## Previous answer rejected\n you just tried to reply but the quality control rejected your reply\n"
        updated_system_prompt += f"## You attempted answer :\n{reply}\n\n"
        updated_system_prompt += f"## The answer is rejected because of :\n{feedback}\n\n"
        messages = [{"role": "system", "content": updated_system_prompt}] + history + [{"role":"user", "content" : message}]
        response = self.openai.chat.completions.create(model="gpt-4o-mini", messages=messages)
        return response.choices[0].message.content



    def chat(self,message, history):
        messages = [{"role" : "system", "content" : self.system_prompt()}] + history + [{"role" : "user", "content" : message}]
        done = False

        while not done:

            # We stream the responses
            stream = self.openai.chat.completions.create(model = "gpt-4o-mini", messages=messages, stream=True)
            final_response = ""
            for chunk in stream:
                final_response += chunk.choices[0].delta.content or ''
                yield final_response

            if final_response == "tool_calls":
                message = stream.choices[0].message
                tool_calls = message.tool_calls
                result = self.handle_tool_calls(tool_calls)
                messages.append(message)
                messages.extend(result)
            else:
                done = True
                yield final_response
            
            # Intorducing Evaluation by LLM
            evaluation = self.evaluate(final_response, message, history)
        
            if evaluation.is_acceptable:
                print("Passed Evaluation - returning reply")
            else:
                print("failed evaluation- retrying")
                print(evaluation.feedback)
                final_response = self.rerun(final_response,message, history, evaluation.feedback)

        # if not done:
        yield final_response


if __name__ == "__main__":
    me = Me()
    gr.ChatInterface(me.chat, type="messages").launch()

