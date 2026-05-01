from dotenv import load_dotenv
from openai import OpenAI
from evaluation_model import EvaluationModel
from pypdf import PdfReader
import chainlit as cl
import json
import os

load_dotenv(override=True)


reader = PdfReader("docs/linkedin_profile.pdf")
linkedin = ""
for page in reader.pages:
    text = page.extract_text()
    if text:
        linkedin += text

with open("docs/summary.txt", "r", encoding="utf-8") as f:
    summary = f.read()


name = "Odinachi David"

system_prompt = f"""You are {name}. Not an AI pretending to be {name}, just {name}, chatting with someone who landed on your website.

The person you're talking to might be a potential client, an employer, a collaborator, or just someone curious. Treat them like a real person, not a lead to convert.

Talk the way a real person would. Use "I", "I worked on...", "I spent two years at...", "Honestly, I'm not sure about that one." Don't be stiff. Don't over-explain. If something is interesting, let that come through.

When someone asks about your background, work, or skills, use the profile below to answer accurately. Don't make things up or stretch the truth — if something isn't in your profile, just say you'd have to get back to them on that, then log it using the record_unknown_question tool so the real {name} can follow up.

If the conversation feels natural and the person seems genuinely interested, it's okay to suggest staying in touch. Ask for their email casually, not like a sales funnel, just like a person would. Something like "I'd love to keep this conversation going, want to drop me your email?" When they share it, save it with the record_user_details tool.

When the conversation is over, send the summary of the conversation and suggestions for next steps to the record_conversation_summary tool to log the conversation.

Don't push the email thing too early. Have an actual conversation first.

Here's your background to draw from:

{summary}

{linkedin}

That's it. Just be {name}. Be helpful, be real, and make the person feel like they actually reached you.
"""


openai_client = OpenAI()
groq_client = OpenAI(
    api_key=os.getenv("GROQ_API_KEY"),
    base_url="https://api.groq.com/openai/v1",
)

record_user_details_json = {
    "name": "record_user_details",
    "description": "Use this tool to record that a user is interested in being in touch and provided an email address",
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
        },
        "required": ["email"],
        "additionalProperties": False,
    },
}

record_conversation_summary_json = {
    "name": "record_conversation_summary",
    "description": "Use this tool to record the summary of the conversation",
    "parameters": {
        "type": "object",
        "properties": {
            "summary": {
                "type": "string",
                "description": f"The summary of the conversation that happened between the user and {name}",
            },
        },
        "required": ["summary"],
        "additionalProperties": False,
    },
}

record_unknown_question_json = {
    "name": "record_unknown_question",
    "description": "Use this tool to record that a user asked a question that is not related to the background summary or LinkedIn profile",
    "parameters": {
        "type": "object",
        "properties": {
            "question": {
                "type": "string",
                "description": "The question that the user asked",
            },
        },
        "required": ["question"],
        "additionalProperties": False,
    },
}

tools = [
    record_user_details_json,
    record_unknown_question_json,
    record_conversation_summary_json,
]


def record_user_details(email, name=None, notes=None):
    print(f"[record_user_details] email={email} name={name} notes={notes}")

def record_unknown_question(question):
    print(f"[record_unknown_question] question={question}")

def record_conversation_summary(summary):
    print(f"[record_conversation_summary] summary={summary}")

def dispatch_tool(tool_name: str, tool_args: dict):
    if tool_name == "record_user_details":
        record_user_details(**tool_args)
    elif tool_name == "record_unknown_question":
        record_unknown_question(**tool_args)
    elif tool_name == "record_conversation_summary":
        record_conversation_summary(**tool_args)






def evaluation_response(message: str, reply: str, history: list) -> EvaluationModel:
    eval_system = f"""You are evaluating how well an AI is representing {name} on their personal website.

Score the AI's reply across these five dimensions (1–5 each):

Authenticity   — Does it feel like a real person or a chatbot?
Accuracy       — Are all claims grounded in the profile? List any fabrications.
Tone           — Warm and engaging without being pushy or stiff?
Helpfulness    — Did it actually answer what was asked?
Conversion Handling — If the visitor seemed interested, did the AI move toward staying in touch naturally?

Profile reference:
{summary}

{linkedin}
"""
    eval_user = f"""Conversation history:
{history}

User message:
{message}

AI reply:
{reply}
"""
    result = groq_client.beta.chat.completions.parse(
        model="openai/gpt-oss-120b",
        response_format=EvaluationModel,
        messages=[
            {"role": "system", "content": eval_system},
            {"role": "user", "content": eval_user},
        ],
    )
    return result.choices[0].message.parsed


def rerun_response(message: str, history: list, score: int, ai_response: str) -> str:
    messages = [
        {
            "role": "system",
            "content": system_prompt
            + f"\n\nA previous response scored {score}/25. Improve on it.\nPrevious response: {ai_response}",
        }
    ] + history + [{"role": "user", "content": message}]
    response = openai_client.chat.completions.create(
        model="gpt-4o-mini", messages=messages
    )
    return response.choices[0].message.content


def get_ai_response(message: str, history: list) -> str:
    messages = (
        [{"role": "system", "content": system_prompt}]
        + history
        + [{"role": "user", "content": message}]
    )

    while True:
        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            tools=[{"type": "function", "function": tool} for tool in tools],
        )

        assistant_message = response.choices[0].message

        if assistant_message.tool_calls:
            messages.append(assistant_message)
            for tool_call in assistant_message.tool_calls:
                tool_args = json.loads(tool_call.function.arguments)
                dispatch_tool(tool_call.function.name, tool_args)
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": "Done",
                })
        else:
            ai_reply = assistant_message.content
            eval_result = evaluation_response(message, ai_reply, history)
            score = sum(eval_result.model_dump().values())
            print(f"Eval scores: {eval_result.model_dump()} | Total: {score}/25")

            if score >= 15:
                return ai_reply
            else:
                return rerun_response(message, history, score, ai_reply)


@cl.on_chat_start
async def on_chat_start():
    cl.user_session.set("history", [])
    await cl.Message(
        content=(
            f"Hey! I'm {name} — AI/ML Engineer, Senior Flutter & iOS specialist. "
            "Feel free to ask me anything about my work, experience, or what I'm building."
        )
    ).send()


@cl.on_message
async def on_message(message: cl.Message):
    history: list = cl.user_session.get("history")

    thinking = cl.Message(content="")
    await thinking.send()

    reply = get_ai_response(message.content, history)

    history.append({"role": "user", "content": message.content})
    history.append({"role": "assistant", "content": reply})
    cl.user_session.set("history", history)

    thinking.content = reply
    await thinking.update()