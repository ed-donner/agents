import os
import shutil
from contextlib import AsyncExitStack
from datetime import datetime
from pathlib import Path
from typing import Any

from agents import Agent, Runner
from agents.mcp import MCPServerStdio

from config import (
    TASKS_FILE,
    TASK_DUE_INTERVAL_DAYS,
    TASK_PLAN_STEPS,
    build_due_schedule,
    iso_today,
)
from task_store import TaskStore
from template import (
    INSTRUCTIONS_TEMPLATE,
    build_check_in_prompt,
    build_mark_done_prompt,
    build_plan_goal_prompt,
)
from dotenv import load_dotenv

load_dotenv(override=True)

class TaskCoach:
    """Autonomous planning coach using task MCP tools and memory MCP."""

    def __init__(self, app_dir: Path):
        self.app_dir = app_dir
        self.memory_dir = app_dir / "memory"
        self.memory_dir.mkdir(parents=True, exist_ok=True)
        self.db_path = self.memory_dir / "coach_memory.db"
        self.uv_path = shutil.which("uv") or "uv"
        self.npx_path = shutil.which("npx") or "npx"
        self.model = "gpt-4.1-mini"
        self.instructions = INSTRUCTIONS_TEMPLATE
        self.store = TaskStore(TASKS_FILE)

    def _task_server_params(self) -> dict[str, Any]:
        return {
            "command": self.uv_path,
            "args": ["run", str(self.app_dir / "task_server.py")],
        }

    def _memory_server_params(self) -> dict[str, Any]:
        env = os.environ.copy()
        env["LIBSQL_URL"] = f"file:{self.db_path}"
        return {
            "command": self.npx_path,
            "args": ["-y", "mcp-memory-libsql"],
            "env": env,
        }

    async def _run_agent(self, prompt: str, max_turns: int = 30) -> str:
        async with AsyncExitStack() as stack:
            task_server = await stack.enter_async_context(
                MCPServerStdio(self._task_server_params(), client_session_timeout_seconds=60)
            )
            memory_server = await stack.enter_async_context(
                MCPServerStdio(self._memory_server_params(), client_session_timeout_seconds=60)
            )
            agent = Agent(
                name="personal_task_coach",
                instructions=self.instructions,
                model=self.model,
                mcp_servers=[task_server, memory_server],
            )
            result = await Runner.run(agent, prompt, max_turns=max_turns)
            return result.final_output

    async def plan_goal(self, goal: str) -> str:
        due_schedule = build_due_schedule(TASK_PLAN_STEPS, TASK_DUE_INTERVAL_DAYS)
        prompt = build_plan_goal_prompt(goal, due_schedule, TASK_DUE_INTERVAL_DAYS)
        return await self._run_agent(prompt)

    async def check_in_and_adapt(self) -> str:
        current_hour = datetime.now().hour
        next_due = build_due_schedule(
            steps=1,
            interval_days=TASK_DUE_INTERVAL_DAYS,
            start_offset_days=TASK_DUE_INTERVAL_DAYS,
        )[0]
        prompt = build_check_in_prompt(current_hour, next_due, TASK_DUE_INTERVAL_DAYS)
        return await self._run_agent(prompt)

    async def mark_done(self, task_id: str, note: str = "") -> str:
        prompt = build_mark_done_prompt(task_id, note)
        return await self._run_agent(prompt)

    def today_tasks(self) -> list[dict[str, Any]]:
        return self.store.get_tasks_by_date(iso_today())
