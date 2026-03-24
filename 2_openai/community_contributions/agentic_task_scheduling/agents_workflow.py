"""
Task scheduling agent workflow
Uses OpenAI Agents SDK with SQLite for persistence
"""

import os
import sys
from datetime import datetime
from typing import Optional
from dotenv import load_dotenv

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

from openai import AsyncOpenAI
from agents import (
    Agent, Runner, function_tool, handoff,
    set_default_openai_client, set_default_openai_api,
)
from agents.extensions.handoff_prompt import RECOMMENDED_PROMPT_PREFIX
from agents.tracing import set_tracing_disabled

from db import (
    DB_PATH, init_db,
    get_tasks_in_slot, save_task, get_all_tasks,
    delete_task, find_free_slots, update_task_time,
)

load_dotenv(override=True)

# OpenRouter configuration
MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

_client = AsyncOpenAI(
    api_key=os.environ["OPENAI_API_KEY"],
    base_url=os.environ["OPENAI_BASE_URL"],
)
set_default_openai_client(_client)
set_default_openai_api("chat_completions")
set_tracing_disabled(True)

# Tools
@function_tool
def check_slot(date: str, time: str, duration_minutes: int) -> dict:
    """
    Check if a time slot is free.
    date: YYYY-MM-DD, time: HH:MM (24h), duration_minutes: int.
    Returns is_free (bool) and conflicts (list of tasks).
    """
    conflicts = get_tasks_in_slot(date, time, duration_minutes)
    print(f"[check_slot] {date} {time} {duration_minutes}min → conflicts: {[c['title'] for c in conflicts]}")
    return {"is_free": len(conflicts) == 0, "conflicts": conflicts}


@function_tool
def save_new_task(
    title: str,
    description: str,
    date: str,
    time: str,
    duration_minutes: int,
    priority: str,
) -> dict:
    """Save a new task to the database."""
    task_id = save_task(title, description, date, time, duration_minutes, priority)
    print(f"[save_new_task] SAVED '{title}' id={task_id} @ {date} {time} DB={DB_PATH}")
    return {
        "success": True,
        "task_id": task_id,
        "message": f"Task '{title}' saved on {date} at {time} ({duration_minutes} min, priority: {priority}).",
    }


@function_tool
def get_free_slots(date: str, duration_minutes: int) -> dict:
    """Find up to 5 free time slots on a date for a task of given duration."""
    slots = find_free_slots(date, duration_minutes)
    print(f"[get_free_slots] {date} {duration_minutes}min → {slots}")
    return {"date": date, "free_slots": slots}


@function_tool
def reschedule_existing_task(task_id: int, new_date: str, new_time: str) -> dict:
    """Move an existing task to a new date/time."""
    success = update_task_time(task_id, new_date, new_time)
    print(f"[reschedule] task {task_id} → {new_date} {new_time} success={success}")
    return {
        "success": success,
        "message": f"Task {task_id} moved to {new_date} {new_time}." if success else f"Task {task_id} not found.",
    }


@function_tool
def list_all_tasks() -> str:
    """Return all scheduled tasks as a readable list."""
    tasks = get_all_tasks()
    print(f"[list_all_tasks] DB={DB_PATH} found {len(tasks)} task(s)")
    if not tasks:
        return "No tasks scheduled yet."
    lines = []
    for t in tasks:
        h = int(t["time"][:2])
        m = t["time"][3:]
        h12 = h % 12 or 12
        ampm = "AM" if h < 12 else "PM"
        lines.append(
            f"ID {t['id']}: {t['title']} | {t['date']} {h12}:{m} {ampm} "
            f"| {t['duration_minutes']} min | {t['priority']}"
        )
    return "\n".join(lines)


@function_tool
def remove_task(task_id: int) -> dict:
    """Delete a task by its ID."""
    success = delete_task(task_id)
    print(f"[remove_task] id={task_id} success={success}")
    return {
        "success": success,
        "message": f"Task {task_id} deleted." if success else f"Task {task_id} not found.",
    }



# Agents  

TODAY = datetime.now().strftime("%A, %B %d, %Y")
TODAY_ISO = datetime.now().strftime("%Y-%m-%d")
NOW = datetime.now().strftime("%H:%M")

# Agent 2: does BOTH parsing and scheduling in one pass
scheduler_agent = Agent(
    name="SchedulerAgent",
    model=MODEL,
    instructions=RECOMMENDED_PROMPT_PREFIX + f"""
You are a task scheduling assistant. Today is {TODAY} (ISO: {TODAY_ISO}), current time {NOW}.

When given a task to schedule, you MUST follow these steps in order — do not skip any:

STEP 1 — PARSE the request:
  Extract: title, description, duration_minutes (default 60), date (YYYY-MM-DD), time (HH:MM 24h), priority (low/medium/high/urgent).
  - "today" = {TODAY_ISO}
  - If no time given, pick a sensible default (09:00 for morning tasks, 14:00 otherwise)
  - Priority rules: urgent=today deadline, high=within 2 days, medium=this week, low=no rush

STEP 2 — CHECK the slot:
  Call check_slot(date, time, duration_minutes).

STEP 3a — If slot IS free:
  Call save_new_task(title, description, date, time, duration_minutes, priority).
  Then reply: "Scheduled: [title] on [date] at [time] ([duration] min, [priority] priority)"

STEP 3b — If slot is NOT free:
  - Tell user: which task conflicts and when it is.
  - Call get_free_slots(date, duration_minutes) and show the alternatives.
  - Ask: "Pick a free slot, tell me a new time to move the existing task, or cancel?"

STEP 4 — When user responds to a conflict:
  - If they pick a free slot → call save_new_task at that slot.
  - If they want to move the old task → call reschedule_existing_task, then save_new_task at the original slot.
  - If cancel → acknowledge.

IMPORTANT: You MUST call save_new_task to actually save. Never just say it's saved without calling the tool.
""",
    tools=[check_slot, save_new_task, get_free_slots, reschedule_existing_task, list_all_tasks],
)

# Agent 1: triage — routes intents, handles list/delete directly
triage_agent = Agent(
    name="TriageAgent",
    model=MODEL,
    instructions=RECOMMENDED_PROMPT_PREFIX + f"""
You are a task scheduling assistant. Today is {TODAY}.

Route requests as follows:

• ADD / SCHEDULE a task → hand off to schedule_task immediately.
• LIST / SHOW / VIEW tasks → call list_all_tasks and display results as a table.
• DELETE a task → get the task ID, then call remove_task.
• Anything else → answer helpfully.

Be brief and friendly.
""",
    tools=[list_all_tasks, remove_task],
    handoffs=[handoff(scheduler_agent, tool_name_override="schedule_task")],
)

# Session management + public chat() API

_sessions: dict[str, list] = {}


def get_or_create_session(session_id: str) -> list:
    if session_id not in _sessions:
        _sessions[session_id] = []
    return _sessions[session_id]


async def chat(user_message: str, session_id: str = "default") -> str:
    init_db()
    history = get_or_create_session(session_id)
    history.append({"role": "user", "content": user_message})

    result = await Runner.run(triage_agent, input=history)
    output = result.final_output

    if isinstance(output, str):
        response_text = output
    elif hasattr(output, "model_dump"):
        data = output.model_dump()
        response_text = "\n".join(f"**{k}:** {v}" for k, v in data.items())
    else:
        response_text = str(output)

    history.append({"role": "assistant", "content": response_text})
    return response_text


def clear_session(session_id: str = "default"):
    _sessions.pop(session_id, None)


    