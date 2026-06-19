import os
import sqlite3
from datetime import datetime
from pathlib import Path

import requests
from dotenv import load_dotenv
from langchain.agents import Tool
from langchain_community.tools.wikipedia.tool import WikipediaQueryRun
from langchain_community.utilities import GoogleSerperAPIWrapper
from langchain_community.utilities.wikipedia import WikipediaAPIWrapper

load_dotenv(override=True)

BASE_DIR = Path(__file__).parent
DB_PATH = BASE_DIR / "client_discovery.db"

pushover_token = os.getenv("PUSHOVER_TOKEN")
pushover_user = os.getenv("PUSHOVER_USER")
pushover_url = "https://api.pushover.net/1/messages.json"
serper_api_key = os.getenv("SERPER_API_KEY")


def get_connection():
    return sqlite3.connect(DB_PATH)


def init_db():
    with get_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS client_runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                thread_id TEXT,
                request_text TEXT NOT NULL,
                success_criteria TEXT,
                company_name TEXT,
                goal TEXT,
                status TEXT,
                created_at TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS clarifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id INTEGER NOT NULL,
                question TEXT NOT NULL,
                answer TEXT,
                created_at TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS client_notes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id INTEGER,
                company_name TEXT,
                note TEXT NOT NULL,
                source TEXT,
                created_at TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS client_briefs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id INTEGER,
                company_name TEXT,
                goal TEXT,
                summary TEXT,
                brief_markdown TEXT NOT NULL,
                file_path TEXT,
                created_at TEXT NOT NULL
            )
            """
        )


def create_run(thread_id: str, request_text: str, success_criteria: str, company_name: str = "", goal: str = "") -> int:
    with get_connection() as conn:
        cur = conn.execute(
            """
            INSERT INTO client_runs (thread_id, request_text, success_criteria, company_name, goal, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (thread_id, request_text, success_criteria, company_name, goal, "in_progress", datetime.utcnow().isoformat()),
        )
        return int(cur.lastrowid)


def update_run(run_id: int, status: str, company_name: str = "", goal: str = ""):
    with get_connection() as conn:
        conn.execute(
            "UPDATE client_runs SET status = ?, company_name = COALESCE(NULLIF(?, ''), company_name), goal = COALESCE(NULLIF(?, ''), goal) WHERE id = ?",
            (status, company_name, goal, run_id),
        )


def save_clarification(run_id: int, question: str, answer: str = ""):
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO clarifications (run_id, question, answer, created_at) VALUES (?, ?, ?, ?)",
            (run_id, question, answer, datetime.utcnow().isoformat()),
        )


def push(text: str):
    if not pushover_token or not pushover_user:
        return "Pushover not configured"
    requests.post(
        pushover_url,
        data={"token": pushover_token, "user": pushover_user, "message": text},
        timeout=20,
    )
    return "success"


def search_web(query: str):
    if not serper_api_key:
        return "SERPER_API_KEY not configured. Web search unavailable."
    wrapper = GoogleSerperAPIWrapper()
    return wrapper.run(query)


def log_client_note(company_name: str, note: str, source: str = "agent", run_id: int = 0):
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO client_notes (run_id, company_name, note, source, created_at) VALUES (?, ?, ?, ?, ?)",
            (run_id or None, company_name, note, source, datetime.utcnow().isoformat()),
        )
    return "note saved"


def search_client_memory(company_name: str):
    with get_connection() as conn:
        notes = conn.execute(
            "SELECT note, source, created_at FROM client_notes WHERE company_name LIKE ? ORDER BY id DESC LIMIT 5",
            (f"%{company_name}%",),
        ).fetchall()
        briefs = conn.execute(
            "SELECT summary, created_at FROM client_briefs WHERE company_name LIKE ? ORDER BY id DESC LIMIT 3",
            (f"%{company_name}%",),
        ).fetchall()
    parts = []
    if notes:
        parts.append("Recent notes:")
        parts.extend([f"- {row[2]} | {row[1]} | {row[0]}" for row in notes])
    if briefs:
        parts.append("Past brief summaries:")
        parts.extend([f"- {row[1]} | {row[0]}" for row in briefs])
    return "\n".join(parts) if parts else f"No saved client memory found for {company_name}."


def save_client_brief(company_name: str, goal: str, summary: str, brief_markdown: str, run_id: int = 0):
    safe_company = "".join(c.lower() if c.isalnum() else "_" for c in company_name).strip("_") or "client"
    filename = f"{safe_company}_brief_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.md"
    file_path = BASE_DIR / filename
    file_path.write_text(brief_markdown, encoding="utf-8")
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO client_briefs (run_id, company_name, goal, summary, brief_markdown, file_path, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (run_id or None, company_name, goal, summary, brief_markdown, str(file_path), datetime.utcnow().isoformat()),
        )
    return str(file_path)


def make_tools():
    push_tool = Tool(
        name="send_push_notification",
        func=push,
        description="Use this tool when you want to send a push notification that a client brief is ready or a task needs attention.",
    )

    search_tool = Tool(
        name="search_web",
        func=search_web,
        description="Use this tool to research companies, products, recent announcements, funding, leadership, or market context on the web.",
    )

    wiki_tool = WikipediaQueryRun(api_wrapper=WikipediaAPIWrapper())

    note_tool = Tool(
        name="log_client_note",
        func=lambda text: log_client_note("", text, "agent"),
        description="Use this tool to save an important client discovery note for later memory. Input should be a concise note string.",
    )

    memory_tool = Tool(
        name="search_client_memory",
        func=search_client_memory,
        description="Use this tool to retrieve past notes or briefs about a company from SQLite memory.",
    )

    return [push_tool, search_tool, wiki_tool, note_tool, memory_tool]
