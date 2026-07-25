from __future__ import annotations

import json
import sys
from contextlib import AsyncExitStack

from agents import Agent, Runner
from agents.mcp import MCPServerStdio

from agent.model import get_model
from agent.prompts import (
    build_draft_user_prompt,
    build_revision_user_prompt,
    draft_system_prompt,
    revision_system_prompt,
)
from services.content import get_content_service


class LinkedInPostAgent:
    def __init__(self) -> None:
        self.content_service = get_content_service()

    async def generate_drafts(
        self,
        topic: str,
        goal: str,
        notes: str = "",
        urls: list[str] | None = None,
    ) -> dict:
        urls = urls or []
        async with AsyncExitStack() as stack:
            servers = [
                await stack.enter_async_context(
                    MCPServerStdio(params, client_session_timeout_seconds=120)
                )
                for params in self._server_params()
            ]
            agent = Agent(
                name="linkedin_post_agent",
                instructions=draft_system_prompt(),
                model=get_model(),
                mcp_servers=servers,
            )
            result = await Runner.run(
                agent,
                build_draft_user_prompt(topic=topic, goal=goal, notes=notes, urls=urls),
                max_turns=25,
            )
        parsed = self._parse_json(result.final_output)
        drafts = self.content_service.list_drafts(limit=10)
        if not parsed.get("draft_ids"):
            parsed["draft_ids"] = [item["id"] for item in drafts[:3]]
        if not parsed.get("bundle_id") and drafts:
            parsed["bundle_id"] = drafts[0]["bundle_id"]
        if not parsed.get("idea_id") and drafts:
            parsed["idea_id"] = drafts[0]["idea_id"]
        return parsed

    async def revise_draft(self, draft_id: str, feedback: str) -> dict:
        async with AsyncExitStack() as stack:
            servers = [
                await stack.enter_async_context(
                    MCPServerStdio(params, client_session_timeout_seconds=120)
                )
                for params in self._server_params()
            ]
            agent = Agent(
                name="linkedin_post_revision_agent",
                instructions=revision_system_prompt(),
                model=get_model(),
                mcp_servers=servers,
            )
            result = await Runner.run(
                agent,
                build_revision_user_prompt(draft_id=draft_id, feedback=feedback),
                max_turns=20,
            )
        parsed = self._parse_json(result.final_output)
        if not parsed.get("revised_draft_id"):
            drafts = self.content_service.list_drafts(limit=10)
            for draft in drafts:
                if draft.get("parent_draft_id") == draft_id:
                    parsed["revised_draft_id"] = draft["id"]
                    break
        return parsed

    def _server_params(self) -> list[dict]:
        modules = [
            "linkedin_post_agent.mcp.linkedin_server",
            "linkedin_post_agent.mcp.research_server",
            "linkedin_post_agent.mcp.content_server",
        ]
        return [{"command": sys.executable, "args": ["-m", module]} for module in modules]

    def _parse_json(self, value: str) -> dict:
        value = value.strip()
        if value.startswith("```"):
            lines = value.splitlines()
            if len(lines) >= 3:
                value = "\n".join(lines[1:-1])
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return {"raw_output": value}
