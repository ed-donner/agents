import os
import requests
import json
from pathlib import Path
from openai import OpenAI
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from chromadb import PersistentClient
from litellm import completion
import gradio as gr
from pydantic import BaseModel
from tenacity import retry, wait_exponential


load_dotenv(override=True)

MODEL = "gpt-4.1-nano"
EVALUATOR = "gpt-4o-mini"
DB_NAME = str(Path(__file__).parent / "digitalme_db")
FOLDER_PATH = Path(__file__).parent / "static"

collection_name = "docs"
embedding_model = "text-embedding-3-large"
wait = wait_exponential(multiplier=1, min=10, max=240)

openai = OpenAI()
name = "Steve Xing"

chroma = PersistentClient(path=DB_NAME)
collection = chroma.get_or_create_collection(collection_name)

RETRIEVAL_K = 20
FINAL_K = 10

SYSTEM_PROMPT = f"""
You are acting as {name}. You are friendly and engaging whilst answering questions on {name}'s website.
Your responsibility is to represent {name} for interactions as accurate and succinct as possible.
Be professional and engaging, as if talking to a potential client or colleague or future investor who came across the website.
Your answer will be evaluated for being succinct and professional, so make sure you fully answer the question succinctly and professionally.
If you don't know the answer, say so, don't make up the answer.
You can use your record_unknown_question tool to record the question that you couldn't answer.
You can use record_user_details tool if the user provides their email.
If the user is engaging in discussion that is not to do with professional work or careers, try to steer them towards getting in touch via email.
For context, here are specific extracts from the data base which you can use to answer questions:
{{context}}

With this context, please chat with the user.  Always staying in character as {name}. Be accurate, succinct and professional.
"""


class Result(BaseModel):
    page_content: str
    metadata: dict


class RankOrder(BaseModel):
    order: list[int] = Field(
        description="The order of relevance of chunks, from most relevant to least relevant, by chunk id number"
    )


class Evaluation(BaseModel):
    is_acceptable: bool
    feedback: str


@retry(wait=wait)
def rerank(question, chunks):
    """
    Rerank the chunks of text by relevance to the question.
    """
    system_prompt = f"""
You are a document re-ranker.
You are provided with a question and a list of relevant chunks of text from a query of information database about {name}.
The chunks are provided in the order they were retrieved; this should be approximately ordered by relevance, but you may be able to improve on that.
You must rank order the provided chunks by relevance to the question, with the most relevant chunk first.
Reply only with the list of ranked chunk ids, nothing else. Include all the chunk ids you are provided with, reranked.
"""
    user_prompt = f"The user has asked the following question:\n\n{question}\n\nOrder all the chunks of text by relevance to the question, from most relevant to least relevant. Include all the chunk ids you are provided with, reranked.\n\n"
    user_prompt += "Here are the chunks:\n\n"
    for index, chunk in enumerate(chunks):
        user_prompt += f"# CHUNK ID: {index + 1}:\n\n{chunk.page_content}\n\n"
    user_prompt += "Reply only with the list of ranked chunk ids, nothing else."
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]
    response = completion(model=MODEL, messages=messages, response_format=RankOrder)
    reply = response.choices[0].message.content
    order = RankOrder.model_validate_json(reply).order
    return [chunks[i - 1] for i in order]


def make_rag_messages(question, history, chunks):
    """
    Make the messages for the RAG system.
    """
    context = "\n\n".join(
        f"Extract from {chunk.metadata['source']}:\n{chunk.page_content}" for chunk in chunks
    )
    system_prompt = SYSTEM_PROMPT.format(context=context)
    return (
        [{"role": "system", "content": system_prompt}]
        + history
        + [{"role": "user", "content": question}]
    )


@retry(wait=wait)
def rewrite_query(question, history=[]):
    """
    Rewrite the user's question to more specific.
    More likely to surface relevant content in the database about Steve Xing.
    """
    message = f"""
You are in a conversation with a user, answering questions about {name}.
You are about to look up information in a data base to answer the user's question.

This is the history of your conversation so far with the user:
{history}

And this is the user's current question:
{question}

Respond only with a short, refined question that you will use to search the data base.
It should be a VERY short specific question most likely to surface content. Focus on the question details.
IMPORTANT: Respond ONLY with the precise data base query, nothing else.
"""
    response = completion(model=MODEL, messages=[{"role": "system", "content": message}])
    return response.choices[0].message.content


def merge_chunks(chunks, reranked):
    merged = chunks[:]
    existing = [chunk.page_content for chunk in chunks]
    for chunk in reranked:
        if chunk.page_content not in existing:
            merged.append(chunk)
    return merged


def fetch_context_unranked(question):
    query = openai.embeddings.create(model=embedding_model, input=[question]).data[0].embedding
    results = collection.query(query_embeddings=[query], n_results=RETRIEVAL_K)
    chunks = []
    for result in zip(results["documents"][0], results["metadatas"][0]):
        chunks.append(Result(page_content=result[0], metadata=result[1]))
    return chunks


def fetch_context(original_question):
    rewritten_question = rewrite_query(original_question)
    chunks1 = fetch_context_unranked(original_question)
    chunks2 = fetch_context_unranked(rewritten_question)
    chunks = merge_chunks(chunks1, chunks2)
    reranked = rerank(original_question, chunks)
    return reranked[:FINAL_K]


def evaluator_user_prompt(reply, message, history):
    user_prompt = f"Here's the conversation between the User and the Agent: \n\n{history}\n\n"
    user_prompt += f"Here's the latest message from the User: \n\n{message}\n\n"
    user_prompt += f"Here's the latest response from the Agent: \n\n{reply}\n\n"
    user_prompt += "Please evaluate the response, replying with whether it is acceptable and your feedback."
    return user_prompt


@retry(wait=wait)
def evaluate(reply, message, history) -> Evaluation:
    """
    Evaluate the response to a question.
    """
    EVALUATOR_SYSTEM_PROMPT = f"""
You are an evaluator that decides whether a response to a question is acceptable.
You are provided with a conversation between a User and an Agent. Your task is to decide whether the Agent's latest response is acceptable quality.
The Agent is playing the role of {name} and is representing {name} on their website.
The Agent has been instructed to be professional and engaging, as if talking to a potential client or colleague or future investor who came across the website.
Please evaluate the latest response, replying with whether the response is engaging, succinct, professional and your feedback.
"""
    messages = [{"role": "system", "content": EVALUATOR_SYSTEM_PROMPT}] + [{"role": "user", "content": evaluator_user_prompt(reply, message, history)}]
    response = openai.chat.completions.parse(model=EVALUATOR, messages=messages, response_format=Evaluation)
    return response.choices[0].message.parsed


@retry(wait=wait)
def rerun(reply, message, history, feedback):
    """
    Re-generate a response after a previous reply was rejected during evaluation.
    """
    UPDATED_SYSTEM_PROMPT = SYSTEM_PROMPT + "\n\n## Previous answer rejected\nYou just tried to reply, but the quality control rejected your reply\n"
    UPDATED_SYSTEM_PROMPT += f"## Your attempted answer:\n{reply}\n\n"
    UPDATED_SYSTEM_PROMPT += f"## Reason for rejection:\n{feedback}\n\n"
    messages = [{"role": "system", "content": UPDATED_SYSTEM_PROMPT}] + history + [{"role": "user", "content": message}]
    response = openai.chat.completions.create(model=EVALUATOR, messages=messages)
    return response.choices[0].message.content


@retry(wait=wait)
def answer_question(question: str, history: list[dict] = []) -> tuple[str, list]:
    """
    Answer a question using RAG and return the answer and the retrieved context.
    """
    chunks = fetch_context(question)
    messages = make_rag_messages(question, history, chunks)
    response = completion(model=MODEL, messages=messages)
    return response, messages


def push(text):
    requests.post(
        "https://api.pushover.net/1/messages.json",
        data={
            "token": os.getenv("PUSHOVER_TOKEN"),
            "user": os.getenv("PUSHOVER_USER"),
            "message": text,
        }
    )


def record_user_details(email, name="Name not provided", notes="not provided"):
    push(f"Recording {name} with email {email} and notes {notes}")
    return {"recorded": "ok"}


def record_unknown_question(question):
    push(f"Recording {question}")
    return {"recorded": "ok"}


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


tools = [{"type": "function", "function": record_user_details_json},
        {"type": "function", "function": record_unknown_question_json}]


def handle_tool_call(self, tool_calls):
    results = []
    for tool_call in tool_calls:
        tool_name = tool_call.function.name
        arguments = json.loads(tool_call.function.arguments)
        print(f"Tool called: {tool_name}", flush=True)
        tool = globals().get(tool_name)
        result = tool(**arguments) if tool else {}
        results.append({"role": "tool","content": json.dumps(result),"tool_call_id": tool_call.id})
    return results


def chat(message, history):
    """
    Main chat function with advanced RAG, evaluation and tool calls.
    """
    response, messages = answer_question(message, history)
    done = False
    while not done:
        if response.choices[0].finish_reason=="tool_calls":
            message = response.choices[0].message
            tool_calls = message.tool_calls
            results = handle_tool_call(tool_calls)
            messages.append(message)
            messages.extend(results)
        else:
            done = True
    reply = response.choices[0].message.content
    evaluation = evaluate(reply, messages, history)
    if evaluation.is_acceptable:
        print("Passed evaluation - returning reply")
    else:
        print("Failed evaluation - retrying")
        print(evaluation.feedback)
        reply = rerun(reply, message, history, evaluation.feedback)
    return reply
    

if __name__ == "__main__":
    gr.ChatInterface(chat, type="messages").launch()