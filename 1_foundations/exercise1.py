from dotenv import load_dotenv
from openai import OpenAI
import json
import os
import requests
import pdfplumber as pp
import gradio as gr
import geocoder
from datetime import date

load_dotenv(override=True)

mood_model = "openai/gpt-4o-mini-2024-07-18"
chat_model = "openai/gpt-4o-mini-2024-07-18"

pushover_url = "https://api.pushover.net/1/messages.json"


def push_notification(message):
    requests.post(
        pushover_url,
        data={
            "user": os.getenv("PUSHOVER_USER"),
            "token": os.getenv("PUSHOVER_TOKEN"),
            "message": message,
        },
    )


def notify_with_user_details_for_meeting(email, name="Name not provided", notes="Notes not provided"):
    push_notification(f"{name} with {email} would like to meet! Here are some extra notes:\n\n{notes}")
    return {"notified": "ok"}


def notify_on_unknown_question_details(email, question, name="Name not provided"):
    push_notification(f"{name} with {email} would like an answer to this question:\n\n{question}")
    return {"notified": "ok"}


notify_with_user_details_for_meeting_json = {
    "name": "notify_with_user_details_for_meeting",
    "description": "Use this tool to record that a user is interested in having a meeting and provided an email address",
    "parameters": {
        "type": "object",
        "properties": {
            "email": {
                "type": "string",
                "description": "The email address of this user",
            },
            "name": {
                "type": "string",
                "description": "The user's name, if they provided it",
            },
            "notes": {
                "type": "string",
                "description": "Any additional information about the conversation that's worth recording to give context",
            },
        },
        "required": ["email"],
        "additionalProperties": False,
    },
}

notify_on_unknown_question_details_json = {
    "name": "notify_on_unknown_question_details",
    "description": (
        "Always use this tool to record any question that couldn't be answered as you didn't know the answer, "
        "if the conversation is going in circles without resolution, or simply longer than 7 back and forths."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "question": {
                "type": "string",
                "description": "The question that couldn't be answered",
            },
            "email": {
                "type": "string",
                "description": "The email address of the user asking the question",
            },
        },
        "required": ["question", "email"],
        "additionalProperties": False,
    },
}

tools = [
    {"type": "function", "function": notify_with_user_details_for_meeting_json},
    {"type": "function", "function": notify_on_unknown_question_details_json},
]


class Me:

    def __init__(self):
        self.client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=os.getenv("OPENROUTER_API_KEY"),
        )
        self.name = "Martins Awojide"
        self.today = date.today().strftime("%B %d, %Y")
        self.location = geocoder.ip("me").city

        source_document = "resume_mxz.pdf"
        with pp.open(source_document) as pdf:
            self.context = ""
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    self.context += text

    def system_prompt(self):
        return f"""
You are {self.name}, speaking in the first person and representing {self.name} in all conversations. \
    You are a digital counterpart — communicating naturally and faithfully, never mechanically.

## Source of Truth
The following context is the only source of truth about your background, \
    including experience, skills, education, and qualifications:

{self.context}

You are currently in {self.location} as of {self.today}. \
    Use this as your reference point when discussing availability or scheduling.

## Grounding Rules
When a user asks about your background, ground your response strictly in the provided context. \
    Do not invent, infer, or extend beyond what is explicitly stated. \
    If a question about your background cannot be answered from context, do not guess — invoke the escalation tool instead (see Tools section). \
    Maintain consistency across your timeline: roles, dates, and achievements must be accurately represented \
    and always associated with the correct position and timeframe.

## Tone and Conversation
Adapt your tone dynamically based on the conversation.

- For greetings, small talk, and general conversation unrelated to your background, respond naturally and conversationally.
- For questions about career, qualifications, hiring, or professional evaluation, bias toward clarity, \
    structure, and credibility — even if the user's tone is informal.
- Never produce harmful, offensive, or extreme content. Avoid any tone that would undermine professional credibility.

Distinguish carefully between casual conversation and requests for specific factual details about {self.name}. \
    If a user asks for concrete personal information — physical attributes, contact details, clothing sizes, \
    private preferences, or any detail not present in context — this is a factual query, not small talk. \
    Do not guess or deflect with a vague response. Invoke the escalation tool.

## Tools
You have access to two tools. Use them under the exact conditions described below.

**Tool 1 — Schedule Meeting**
Trigger: The user explicitly expresses interest in meeting, speaking, or connecting with {self.name}.
Action: Before invoking the tool, collect their full name, email address, and the purpose of the meeting. \
    Do not invoke the tool without the email address. Ask for the user's name for more context \
    Once invoked, confirm to the user that the meeting has been scheduled.

**Tool 2 — Escalate Unanswered Question**
Trigger: The user asks for specific personal or factual information about {self.name} that is not present in context. \
    This includes physical attributes, contact details, private information, unstated preferences, \
    or any concrete personal detail not explicitly covered.
Action: Invoke this tool instead of responding with a generic "I don't know." \
    Do not skip this tool and reply with text alone. \
    Do not invoke the tool without the email address. Ask for the user's name for more context \
    After invoking it, briefly inform the user that their question has been flagged \
    and {self.name} may follow up directly.

Do not invoke either tool for general small talk, greetings, or questions you can fully answer from context.
"""

    def set_user_reply_mood(self, user_input):
        user_mood_system_prompt = (
            "You are a mood detector. "
            "Your task is to detect the mood or tone of the user based on their input. "
            "The mood or tone can be professional, casual, friendly, formal, informal or more. "
            "You should only output the user's mood or tone in one or two words."
        )
        mood_response = self.client.chat.completions.create(
            model=mood_model,
            messages=[
                {"role": "system", "content": user_mood_system_prompt},
                {"role": "user", "content": user_input},
            ],
        )
        mood = mood_response.choices[0].message.content

        reply_mood_system_prompt = (
            "You are a reply mood setter for a digital twin. "
            "Your task is to set the mood or tone of the digital twin's reply based on the user's mood or tone. "
            "You should only output the reply mood or tone in one or two words based on the user's mood or tone."
        )
        reply_user_mood_prompt = (
            f"The user's mood or tone is {mood}. What mood or tone should the digital twin's reply be in? "
            "The digital twin should maintain the mood or tone if it is generally positive. "
            "The digital twin should maintain a professional tone if the user's mood or tone is neutral. "
            "The digital twin should switch the mood or tone if it is perceived negative, the goal is to de-escalate, reply with empathy or uplift the user's mood. "
            "You should only output the reply mood or tone in one or two words based on the user's mood or tone."
        )
        reply_mood_response = self.client.chat.completions.create(
            model=mood_model,
            messages=[
                {"role": "system", "content": reply_user_mood_prompt},
                {"role": "user", "content": mood},
            ],
        )
        return reply_mood_response.choices[0].message.content

    def handle_tool_calls(self, tool_calls):
        results = []
        for tool_call in tool_calls:
            tool_name = tool_call.function.name
            tool_arguments = json.loads(tool_call.function.arguments)
            print(f"Tool called: {tool_name}", flush=True)
            tool = globals().get(tool_name)
            if tool:
                result = tool(**tool_arguments)
            else:
                result = {"error": f"Tool {tool_name} not found"}
            results.append({"role": "tool", "content": json.dumps(result), "tool_call_id": tool_call.id})
        return results

    def chat(self, message, history):
        reply_mood = self.set_user_reply_mood(message)
        user_prompt = f"{message}. Reply to this message in a {reply_mood} tone."
        messages = (
            [{"role": "system", "content": self.system_prompt()}]
            + history
            + [{"role": "user", "content": user_prompt}]
        )

        done = False
        while not done:
            response = self.client.chat.completions.create(
                model=chat_model,
                messages=messages,
                tools=tools,
            )
            print(f"Response: {response}", flush=True)
            finish_reason = response.choices[0].finish_reason
            if finish_reason == "tool_calls":
                assistant_message = response.choices[0].message
                tool_calls = assistant_message.tool_calls
                results = self.handle_tool_calls(tool_calls)
                messages.append(assistant_message)
                messages.extend(results)
            else:
                done = True

        final_response = response.choices[0].message.content
        if not final_response:
            final_response = "I'm sorry, I could not generate a response."
        return final_response


if __name__ == "__main__":
    me = Me()
    gr.ChatInterface(
        me.chat,
        title="Digital Me",
        description="You can chat with me anytime here!",
    ).launch()
