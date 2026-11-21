import json
import os
import requests
import database
from knowledge_base import KnowledgeBase

pushover_user = os.getenv("PUSHOVER_USER")
pushover_token = os.getenv("PUSHOVER_TOKEN")
pushover_url = "https://api.pushover.net/1/messages.json"


def push(text):
    print(f"Push: {text}", flush=True)
    if not (pushover_user and pushover_token):
        return
    try:
        requests.post(pushover_url, data={"token": pushover_token, "user": pushover_user, "message": text}, timeout=10)
    except requests.RequestException as error:
        print(f"Pushover failed: {error}", flush=True)


search_knowledge_base_json = {
    "name": "search_knowledge_base",
    "description": "Search the documents about Sebastian (LinkedIn profile, CV, notes). "
    "Use it before stating any fact about his career, skills, education or availability. "
    "The documents are written in English, so always write the query in English.",
    "parameters": {
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "English keywords for what you are looking for, e.g. 'certifications' or 'automation tools skills'"}
        },
        "required": ["query"],
        "additionalProperties": False,
    },
}

search_faq_json = {
    "name": "search_faq",
    "description": "Look up previously approved answers to common questions in the FAQ SQL database.",
    "parameters": {
        "type": "object",
        "properties": {"query": {"type": "string", "description": "The visitor's question or its key words"}},
        "required": ["query"],
        "additionalProperties": False,
    },
}

save_faq_json = {
    "name": "save_faq",
    "description": "Store a common question and the answer you gave in the FAQ SQL database, so future visitors get a consistent answer. "
    "Only use it for answers fully supported by the knowledge base, never for answers saying you don't know.",
    "parameters": {
        "type": "object",
        "properties": {
            "question": {"type": "string", "description": "A short, general version of the question, e.g. 'What certifications does Sebastian have?'"},
            "answer": {"type": "string", "description": "The answer, using only verified facts"},
        },
        "required": ["question", "answer"],
        "additionalProperties": False,
    },
}

record_user_details_json = {
    "name": "record_user_details",
    "description": "Use this tool to record that a user is interested in being in touch and provided an email address",
    "parameters": {
        "type": "object",
        "properties": {
            "email": {"type": "string", "description": "The email address of this user"},
            "name": {"type": "string", "description": "The user's name, if they provided it"},
            "notes": {"type": "string", "description": "Any additional info about the conversation that's worth recording to give context"},
        },
        "required": ["email"],
        "additionalProperties": False,
    },
}

record_unknown_question_json = {
    "name": "record_unknown_question",
    "description": "Always use this tool to record any question that couldn't be answered as you didn't know the answer",
    "parameters": {
        "type": "object",
        "properties": {"question": {"type": "string", "description": "The question that couldn't be answered"}},
        "required": ["question"],
        "additionalProperties": False,
    },
}

tools = [
    {"type": "function", "function": definition}
    for definition in (
        search_knowledge_base_json,
        search_faq_json,
        save_faq_json,
        record_user_details_json,
        record_unknown_question_json,
    )
]


class ToolRunner:
    """Runs the tools for one answer attempt.

    It keeps the evidence the twin retrieved (so the evaluator can check the answer against it)
    and holds every database write until the answer is approved.
    """

    def __init__(self, knowledge: KnowledgeBase):
        self.knowledge = knowledge
        self.tool_map = {
            "search_knowledge_base": self.search_knowledge_base,
            "search_faq": self.search_faq,
            "save_faq": self.save_faq,
            "record_user_details": self.record_user_details,
            "record_unknown_question": self.record_unknown_question,
        }
        self.evidence = []
        self.actions = []
        self.pending_faqs = []
        self.pending_contacts = []
        self.pending_unknown_questions = []

    def search_knowledge_base(self, query):
        results = self.knowledge.search(query)
        self.evidence.extend(f"[{result['source']}]\n{result['text']}" for result in results)
        return results or "No matching documents. Try other English keywords."

    def search_faq(self, query):
        results = database.search_faq(query)
        self.evidence.extend(f"[FAQ database]\nQ: {result['question']}\nA: {result['answer']}" for result in results)
        return results or "No matching FAQ entries."

    def save_faq(self, question, answer):
        self.pending_faqs.append((question, answer))
        return "OK"

    def record_user_details(self, email, name="Name not provided", notes="not provided"):
        self.pending_contacts.append((email, name, notes))
        return "OK"

    def record_unknown_question(self, question):
        self.pending_unknown_questions.append(question)
        return "OK"

    def handle_tool_calls(self, tool_calls):
        results = []
        for tool_call in tool_calls:
            tool_name = tool_call.function.name
            arguments = json.loads(tool_call.function.arguments)
            print(f"Tool called: {tool_name} {arguments}", flush=True)
            self.actions.append(f"{tool_name}({json.dumps(arguments, ensure_ascii=False)})")
            tool = self.tool_map.get(tool_name)
            result = tool(**arguments) if tool else "Unknown tool: " + tool_name
            results.append(
                {"role": "tool", "content": json.dumps(result, ensure_ascii=False), "tool_call_id": tool_call.id}
            )
        return results

    def commit(self, include_faqs=True):
        if include_faqs:
            for question, answer in self.pending_faqs:
                database.save_faq(question, answer)
        for email, name, notes in self.pending_contacts:
            database.record_contact(email, name, notes)
            push(f"Recording interest from {name} with email {email} and notes {notes}")
        for question in self.pending_unknown_questions:
            database.record_unknown_question(question)
            push(f"Recording {question} asked that I couldn't answer")
