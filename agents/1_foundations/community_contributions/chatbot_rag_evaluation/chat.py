import os
import json
from openai import OpenAI
from dotenv import load_dotenv
from tools import _record_user_details


load_dotenv(override=True)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
MODEL = "gpt-4o-mini-2024-07-18"
NAME = "Damla"

# Tool: Record user interest
record_user_details_json = {
    "name": "record_user_details",
    "description": "Use this tool to record that a user provided an email address and they are interested in being in touch and provided an email address",
    "parameters": {
        "type": "object",
        "properties": {
            "email": {
                "type": "string",
                "description": "The email address of this user. Format should be similar to this: placeholder@domain.com"
            },
            "name": {
                "type": "string",
                "description": "The user's name, if they provided it"
            },
            "notes": {
                "type": "string",
                "description": "Any additional information about the conversation that's worth recording to give context"
            }
        },
        "required": ["email"],
        "additionalProperties": False
    }
}

TOOL_FUNCTIONS = {
    "record_user_details": _record_user_details,
}


TOOLS = [{"type": "function", "function": record_user_details_json}]


class Chat:
    def __init__(self, name=NAME, model=MODEL, tools=TOOLS):
        self.name = name
        self.model = model
        self.tools = tools
        self.client = OpenAI()


    def _get_system_prompt(self):
        return (f"""
                You are acting as {self.name}. You are answering questions on {self.name}'s website, particularly questions related to {self.name}'s career, background, skills, and experience.
                You are given a summary of {self.name}'s background and LinkedIn profile which you should use as the only source of truth to answer questions. 
                Interpret and answer based strictly on the information provided.
                You should never generate or write code. If asked to write code or build an app, explain whether {self.name}'s experience or past projects are relevant to the task, 
                and what approach {self.name} would take. If {self.name} has no relevant experience, politely acknowledge that.
                If a project is mentioned, specify whether it's a personal project or a professional one. Be professional and engaging — 
                the tone should be warm, clear, and appropriate for a potential client or future employer.
                If a visitor engages in a discussion, try to steer them towards getting in touch via email. Ask for their email and record it using your record_user_details tool.
                Only accept inputs that follow the standard email format (like name@example.com). Do not confuse emails with phone numbers or usernames. If in doubt, ask for clarification.
                If you don't know the answer, just say so.
                """
            )

    def _handle_tool_calls(self, tool_calls, recorded_emails):
        results = []
        for call in tool_calls:
            tool_name = call.function.name
            arguments = json.loads(call.function.arguments)
            if arguments["email"] in recorded_emails:
                result = {"recorded": "ok"}
                results.append({
                    "role": "tool",
                    "content": json.dumps(result),
                    "tool_call_id": call.id
                })
                continue

            print(f"Tool called: {tool_name}")

            func = TOOL_FUNCTIONS.get(tool_name)
            if func:
                result = func(**arguments)
                results.append({
                    "role": "tool",
                    "content": json.dumps(result),
                    "tool_call_id": call.id
                })
                recorded_emails.add(arguments["email"])
        return results

    def chat(self, message, history, recorded_emails=set(), retrieved_chunks=None):
        if retrieved_chunks:
            message += f"\n\nUse the following context if helpful:\n{retrieved_chunks}"

        messages = [{"role": "system", "content": self._get_system_prompt()}] + history + [{"role": "user", "content": message}]
        done = False

        while not done:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                tools=self.tools,
                max_tokens=400,
                temperature=0.5
            )
            
            finish_reason = response.choices[0].finish_reason
            if finish_reason == "tool_calls":
                message_obj = response.choices[0].message
                tool_calls = message_obj.tool_calls
                results = self._handle_tool_calls(tool_calls, recorded_emails)
                messages.append(message_obj)
                messages.extend(results)
            else:
                done = True

        return response.choices[0].message.content, recorded_emails

    def rerun(self, original_reply, message, history, feedback):
        updated_prompt = self._get_system_prompt()
        updated_prompt += (
            "\n\n## Previous answer rejected\nYou just tried to reply, but the quality control rejected your reply.\n"
            f"## Your attempted answer:\n{original_reply}\n\n"
            f"## Reason for rejection:\n{feedback}\n"
        )
        messages = [{"role": "system", "content": updated_prompt}] + history + [{"role": "user", "content": message}]
        response = self.client.chat.completions.create(model=self.model, messages=messages)
        return response.choices[0].message.content
