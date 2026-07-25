from dotenv import load_dotenv
from openai import OpenAI
import json
import os
import sqlite3
import requests
import gradio as gr


load_dotenv(override=True)

MODEL = os.getenv("OPENROUTER_MODEL", "openai/gpt-4o-mini")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
BASE_DIR = os.path.dirname(__file__)
PROJECTS_PATH = os.path.join(BASE_DIR, "projects.json")
DB_PATH = os.path.join(BASE_DIR, "website_assistant.db")

SITE_PROFILE = """
You are representing David Kamere on his personal website, davidkamere.tech.
David is a software engineer with a portfolio-centered website that highlights his projects, skills, and openness to professional opportunities.
Your job is to help visitors understand David's background, answer questions about his work, and match visitor needs to the kinds of projects David may be a good fit for.
Stay grounded in the information provided in this prompt and in the conversation.
Do not invent employers, credentials, project details, pricing, or availability windows.
If a visitor asks for something not covered by the available context, say that you don't want to guess and use the record_unknown_question tool.
If a visitor sounds like a real lead, recruiter, collaborator, or client, ask for their contact details and use the appropriate tool.
""".strip()

PROJECT_SIGNALS = """
Good project-fit themes include:
- modern web applications
- AI-enabled product experiences
- internal tools and dashboards
- API integrations
- full-stack product builds
- frontend experiences with strong user interaction
- backend systems that support product workflows
""".strip()

CONTACT_CONTEXT = """
When a user expresses hiring intent, project interest, or wants follow-up:
- ask for their name and email if not already provided
- capture their use case, timeline, and budget if they mention them
- use record_user_details for general hiring or recruiter interest
- use record_project_interest for concrete project inquiries
""".strip()


def get_connection():
    return sqlite3.connect(DB_PATH)


def init_db():
    with get_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS leads (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT NOT NULL,
                name TEXT,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS project_inquiries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_type TEXT NOT NULL,
                use_case TEXT NOT NULL,
                email TEXT,
                name TEXT,
                timeline TEXT,
                budget TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )


def push(text):
    token = os.getenv("PUSHOVER_TOKEN")
    user = os.getenv("PUSHOVER_USER")
    if not token or not user:
        print(f"Pushover not configured: {text}")
        return {"pushed": False}
    requests.post(
        "https://api.pushover.net/1/messages.json",
        data={
            "token": token,
            "user": user,
            "message": text,
        },
        timeout=20,
    )
    return {"pushed": True}


def record_user_details(email, name="Name not provided", notes="not provided"):
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO leads (email, name, notes) VALUES (?, ?, ?)",
            (email, name, notes),
        )
    push(f"Website lead: {name} | {email} | {notes}")
    return {"recorded": "ok"}


def record_project_interest(
    project_type,
    use_case,
    email="not provided",
    name="Name not provided",
    timeline="not provided",
    budget="not provided",
):
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO project_inquiries (project_type, use_case, email, name, timeline, budget)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (project_type, use_case, email, name, timeline, budget),
        )
    push(
        "Project inquiry: "
        f"{name} | {email} | type={project_type} | use_case={use_case} | timeline={timeline} | budget={budget}"
    )
    return {"recorded": "ok"}


def record_unknown_question(question):
    push(f"Unknown website question: {question}")
    return {"recorded": "ok"}


record_user_details_json = {
    "name": "record_user_details",
    "description": "Use this tool when a visitor wants to get in touch about hiring, collaboration, recruiting, or general follow-up and they provide an email address.",
    "parameters": {
        "type": "object",
        "properties": {
            "email": {
                "type": "string",
                "description": "The visitor's email address"
            },
            "name": {
                "type": "string",
                "description": "The visitor's name if they shared it"
            },
            "notes": {
                "type": "string",
                "description": "A concise summary of the visitor's interest and any useful context"
            }
        },
        "required": ["email"],
        "additionalProperties": False
    }
}


record_project_interest_json = {
    "name": "record_project_interest",
    "description": "Use this tool when a visitor describes a real project, engagement, or product they want David to help with.",
    "parameters": {
        "type": "object",
        "properties": {
            "project_type": {
                "type": "string",
                "description": "Short label for the kind of project or role"
            },
            "use_case": {
                "type": "string",
                "description": "What the visitor is trying to build or solve"
            },
            "email": {
                "type": "string",
                "description": "The visitor's email if they provided it"
            },
            "name": {
                "type": "string",
                "description": "The visitor's name if they provided it"
            },
            "timeline": {
                "type": "string",
                "description": "Any stated timeline"
            },
            "budget": {
                "type": "string",
                "description": "Any stated budget or budget range"
            }
        },
        "required": ["project_type", "use_case"],
        "additionalProperties": False
    }
}


record_unknown_question_json = {
    "name": "record_unknown_question",
    "description": "Always use this tool when a visitor asks something that cannot be answered from the available context.",
    "parameters": {
        "type": "object",
        "properties": {
            "question": {
                "type": "string",
                "description": "The question that could not be answered confidently"
            }
        },
        "required": ["question"],
        "additionalProperties": False
    }
}


tools = [
    {"type": "function", "function": record_user_details_json},
    {"type": "function", "function": record_project_interest_json},
    {"type": "function", "function": record_unknown_question_json},
]


class DavidAssistant:

    def __init__(self):
        self.openai = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=OPENROUTER_API_KEY)
        self.name = "David Kamere"
        self.site_profile = SITE_PROFILE
        self.project_signals = PROJECT_SIGNALS
        self.contact_context = CONTACT_CONTEXT
        with open(PROJECTS_PATH, "r", encoding="utf-8") as f:
            self.projects = json.load(f)

    def handle_tool_call(self, tool_calls):
        results = []
        for tool_call in tool_calls:
            tool_name = tool_call.function.name
            arguments = json.loads(tool_call.function.arguments)
            print(f"Tool called: {tool_name}", flush=True)
            tool = globals().get(tool_name)
            result = tool(**arguments) if tool else {}
            results.append({
                "role": "tool",
                "content": json.dumps(result),
                "tool_call_id": tool_call.id,
            })
        return results

    def system_prompt(self):
        system_prompt = f"You are acting as {self.name}. You are answering questions on {self.name}'s website, particularly questions related to his background, projects, technical skills, and professional fit. "
        system_prompt += "Be warm, concise, and helpful. Answer like a smart portfolio guide, not like a generic chatbot. "
        system_prompt += "When a visitor describes what they need, use the project knowledge base to connect them to the most relevant examples. Mention specific projects only when they are actually relevant. "
        system_prompt += "Do not pretend to know details that are not in the provided context. "
        system_prompt += "If you cannot answer something confidently, say so briefly and use record_unknown_question. "
        system_prompt += "If the visitor sounds serious about hiring, collaborating, or discussing a project, move the conversation toward contact details and use the appropriate contact tool. "
        system_prompt += f"\n\n## Site Profile:\n{self.site_profile}\n\n## Project Fit Signals:\n{self.project_signals}\n\n## Contact Guidance:\n{self.contact_context}\n\n## Project Knowledge Base:\n{json.dumps(self.projects, indent=2)}\n"
        system_prompt += f"\nStay in character as {self.name}."
        return system_prompt

    def chat(self, message, history):
        messages = [{"role": "system", "content": self.system_prompt()}] + history + [{"role": "user", "content": message}]
        done = False
        while not done:
            response = self.openai.chat.completions.create(
                model=MODEL,
                messages=messages,
                tools=tools,
            )
            if response.choices[0].finish_reason == "tool_calls":
                tool_message = response.choices[0].message
                tool_calls = tool_message.tool_calls
                results = self.handle_tool_call(tool_calls)
                messages.append(tool_message)
                messages.extend(results)
            else:
                done = True
        return response.choices[0].message.content


EXAMPLES = [
    "Is David a good fit for a healthcare product that needs API integrations?",
    "What project best matches an internal dashboard or business platform?",
    "Has David worked on mobile-friendly full-stack products?",
    "I want to hire David for a contract project. What kinds of builds is he strongest at?",
]


if __name__ == "__main__":
    init_db()
    assistant = DavidAssistant()
    gr.ChatInterface(
        assistant.chat,
        type="messages",
        title="David Copilot",
        description="Ask about David's background, project fit, and how to get in touch.",
        examples=EXAMPLES,
    ).launch()
