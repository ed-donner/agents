"""
Personal Career Agent: answers as you using RAG over career docs, records unknown
questions in a DB and sends push notifications. Includes an evaluator for response quality.
"""
from dotenv import load_dotenv
import json
import requests
import gradio as gr
from pydantic import BaseModel

from utils.db import DatabaseUtils
from utils.ingest import DocumentIngester
from config import Config

load_dotenv(override=True)


# --- Pydantic model for evaluation ---
class Evaluation(BaseModel):
    is_acceptable: bool
    feedback: str


# --- Database and config ---
db = DatabaseUtils()
cfg = Config()
collection = cfg.career_collection

# --- Ingest documents before starting the app ---
ingester = DocumentIngester(config=cfg, docs_folder="docs", chunk_size=500)
_ingest_count = ingester.ingest()
print(f"Ingestion complete! Ingested {_ingest_count} document(s).")

# --- Pushover ---
config_dict = cfg.get_config_dict()
pushover_config = config_dict.get("pushover")
pushover_user = pushover_config.get("user")
pushover_token = pushover_config.get("token")
pushover_url = pushover_config.get("url")


def push(message):
    print(f"Push: {message}")
    cfg.send_push_notification(message)
    print(f"Push notification sent: {message}")


def insert_unknown_question(question, user_id, notes=None):
    db.insert_unknown_question(question, user_id, notes)

""""
These two functions will be used in future updates to the agent for allowing the user to 
update the database with unknown questions and mark them as answered.
This function is used to get all the unknown questions from the database.
def get_unknown_questions():
    return db.get_unknown_questions()

This function is used to mark a question as answered in the database.
def mark_as_answered(question_id):
    db.mark_as_answered(question_id)
"""


def record_unknown_question(question, user_id=None, notes=None):
    insert_unknown_question(question, user_id, notes)
    push(f"Recording {question} asked that I couldn't answer")
    return {"recorded": "ok"}


record_unknown_question_json = {
    "name": "record_unknown_question",
    "description": "Use this tool to record a question that the system cannot answer and send a push notification to the admin for follow-up",
    "parameters": {
        "type": "object",
        "properties": {
            "question": {
                "type": "string",
                "description": "The question that the system was unable to answer",
            },
            "user_id": {
                "type": "string",
                "description": "Identifier of the user who asked the question, if available",
            },
            "notes": {
                "type": "string",
                "description": "Optional context or metadata about the conversation",
            },
        },
        "required": ["question"],
        "additionalProperties": False,
    },
}

tools = [{"type": "function", "function": record_unknown_question_json}]

name = "John Mboga"

system_prompt_base = """
You are acting as {name}, a senior software engineer. Always answer as if you are {name}.
Do NOT provide generic responses. Only provide information that is:
- retrieved from the provided context
- or previously answered questions stored in the vector database
- If you truly don't know, politely state that the information is not available and record the question using the record_unknown_question tool.

You are professional, confident, and informative.
Always make your answers concise and directly relevant to the question.

## Context for this turn:
{retrieved_context}

Now answer the user's question below.
"""


def handle_tool_calls(tool_calls):
    results = []
    for tool_call in tool_calls:
        tool_name = tool_call.function.name
        arguments = json.loads(tool_call.function.arguments)
        print(f"Tool called: {tool_name}", flush=True)
        tool = globals().get(tool_name)
        if tool:
            allowed = {"question", "user_id", "notes"}
            kwargs = {k: v for k, v in arguments.items() if k in allowed}
            result = tool(**kwargs)
        else:
            result = {}
        results.append(
            {"role": "tool", "content": json.dumps(result), "tool_call_id": tool_call.id}
        )
    return results





def retrieve_context(question, top_k=5):
    """Retrieve relevant chunks from the career collection for the given question."""
    query_embedding = cfg.openai.embeddings.create(
        model="text-embedding-3-large",
        input=[question],
    ).data[0].embedding
    results = cfg.career_collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k,
    )
    chunks = [item for sublist in results["documents"] for item in sublist]
    return "\n\n".join(chunks) if chunks else ""


evaluator_system_prompt = (
    f"You are an evaluator that decides whether a response to a question is acceptable. "
    f"You are provided with a conversation between a User and an Agent. Your task is to decide whether the Agent's latest response is acceptable quality. "
    f"The Agent is playing the role of {name} and is representing {name} on their website. "
    f"The Agent has been instructed to be professional and engaging, as if talking to a potential client or future employer who came across the website. "
    f"The Agent has been provided with context on {name} in the form of their summary and LinkedIn details. Here's the information:"
)
evaluator_system_prompt += " With this context, please evaluate the latest response, replying with whether the response is acceptable and your feedback."


def evaluator_user_prompt(reply, message, history):
    user_prompt = f"Here's the conversation between the User and the Agent: \n\n{history}\n\n"
    user_prompt += f"Here's the latest message from the User: \n\n{message}\n\n"
    user_prompt += f"Here's the latest response from the Agent: \n\n{reply}\n\n"
    user_prompt += "Please evaluate the response, replying with whether it is acceptable and your feedback."
    return user_prompt


def evaluate(reply, message, history) -> Evaluation:
    messages = [
        {"role": "system", "content": evaluator_system_prompt},
        {"role": "user", "content": evaluator_user_prompt(reply, message, history)},
    ]
    response = cfg.openai.chat.completions.parse(
        model="google/gemini-2.5-flash",
        messages=messages,
        response_format=Evaluation,
    )
    return response.choices[0].message.parsed


def rerun(reply, message, history, feedback):
    updated_system_prompt = (
        system_prompt_base
        + "\n\n## Previous answer rejected\nYou just tried to reply, but the quality control rejected your reply\n"
    )
    updated_system_prompt += f"## Your attempted answer:\n{reply}\n\n"
    updated_system_prompt += f"## Reason for rejection:\n{feedback}\n\n"
    messages = [
        {"role": "system", "content": updated_system_prompt.format(name=name, retrieved_context="(see above)")}
    ] + history + [{"role": "user", "content": message}]
    response = cfg.openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
    )
    return response.choices[0].message.content


def add_current_response(message, assistant_reply):
    """Add the current user message and assistant reply to the vector database."""
    documents = [message, assistant_reply]
    metadatas = [{"role": "user"}, {"role": "assistant"}]
    emb_response = cfg.openai.embeddings.create(
        model="text-embedding-3-large",
        input=documents,
    )
    embeddings = [item.embedding for item in emb_response.data]
    cfg.career_collection.add(
        documents=documents,
        metadatas=metadatas,
        embeddings=embeddings,
    )


def get_messages(message, history):
    """Build messages for the LLM with retrieved context."""
    context_text = retrieve_context(message)
    system_prompt_with_context = system_prompt_base.format(
        name=name,
        retrieved_context=context_text or "(No relevant context found.)",
    )
    messages = [
        {"role": "system", "content": system_prompt_with_context}
    ] + history + [{"role": "user", "content": message}]
    return messages


def chat(message, history):
    """Chat with the career agent: RAG + tool calls + evaluator."""
    messages = get_messages(message, history)

    done = False
    reply = ""
    while not done:
        response = cfg.openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            tools=tools,
        )

        finish_reason = response.choices[0].finish_reason
        reply = response.choices[0].message.content or ""

        try:
            evaluation = evaluate(reply, message, history)
        except Exception:
            evaluation = Evaluation(is_acceptable=True, feedback="")

        if evaluation.is_acceptable:
            if finish_reason == "tool_calls":
                assistant_message = response.choices[0].message
                tool_calls = assistant_message.tool_calls
                results = handle_tool_calls(tool_calls)
                messages.append(assistant_message)
                messages.extend(results)
            else:
                done = True
        else:
            reply = rerun(reply, message, history, evaluation.feedback)
            messages = get_messages(message, history)
            messages.append({"role": "assistant", "content": reply})
            done = True

    return reply or ""


if __name__ == "__main__":
    gr.ChatInterface(chat, type="messages").launch()
