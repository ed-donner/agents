from __future__ import annotations

import os
from contextlib import AsyncExitStack
from pathlib import Path
from typing import List, Optional

from dotenv import load_dotenv
from pydantic import BaseModel

load_dotenv()


class AgentSpec(BaseModel):
    name: str
    role: str
    instructions: str
    handoff_description: str = ""
    tools: List[str] = []
    mcp_servers: List[dict] = []


class TeamSpec(BaseModel):
    manager: AgentSpec
    specialists: List[AgentSpec]
    success_criteria: List[str]
    domain: str = "general"
    generated_dir: Optional[str] = None
    primary_language: Optional[str] = None


def sanitize_name(name: str) -> str:
    return "".join(c if c.isalnum() else "_" for c in (name or "agent").lower())


def week6_mcp_root(project_dir: Path) -> Path:
    env = os.getenv("WEEK6_MCP_ROOT")
    if env:
        return Path(env).resolve()
    # project_dir = .../chrys/generated_teams/<slug>
    # .../6_mcp/community_contributions/chrys/generated_teams/<slug>
    return project_dir.resolve().parents[4]


def build_stdio_params(
    tool_id: str,
    agent_slug: str,
    *,
    week6: Path,
    memory_parent: Path,
) -> dict | None:
    tid = (tool_id or "").strip().lower().replace(" ", "_").replace("-", "_")
    if tid == "fetch":
        return {"command": "uvx", "args": ["mcp-server-fetch"]}
    if tid in ("duckduckgo", "duckduckgo_search", "ddg_search"):
        # Pin upstream that speaks clean JSON-RPC on stdout (some PyPI builds log config to stdout).
        return {
            "command": "uvx",
            "args": [
                "--from",
                "git+https://github.com/nickclyde/duckduckgo-mcp-server",
                "duckduckgo-mcp-server",
            ],
        }
    if tid in ("playwright", "browser"):
        return {
            "command": "npx",
            "args": ["-y", "@playwright/mcp@latest"],
        }
    if tid == "serper" and (os.getenv("SERPER_API_KEY") or os.getenv("SERPAPI_API_KEY")):
        key = os.getenv("SERPER_API_KEY") or os.getenv("SERPAPI_API_KEY") or ""
        return {
            "command": "uvx",
            "args": ["serper-mcp-server"],
            "env": {"SERPER_API_KEY": key},
        }
    if tid == "memory":
        memory_parent.mkdir(parents=True, exist_ok=True)
        db_path = (memory_parent / f"{agent_slug}.db").resolve()
        return {
            "command": "npx",
            "args": ["-y", "mcp-memory-libsql"],
            "env": {"LIBSQL_URL": f"file:{db_path}"},
        }
    if tid == "pushover" and os.getenv("PUSHOVER_USER") and os.getenv("PUSHOVER_TOKEN"):
        return {"command": "uv", "args": ["run", "push_server.py"], "cwd": str(week6)}
    if tid == "resend" and os.getenv("RESEND_API_KEY"):
        return {
            "command": "npx",
            "args": ["-y", "resend-mcp"],
            "env": {"RESEND_API_KEY": os.getenv("RESEND_API_KEY", "")},
        }
    if tid == "alphavantage" and os.getenv("ALPHAVANTAGE_API_KEY"):
        return {
            "command": "npx",
            "args": ["-y", "alphavantage-stock-mcp"],
            "env": {"ALPHAVANTAGE_API_KEY": os.getenv("ALPHAVANTAGE_API_KEY", "")},
        }
    return None


def effective_tool_ids(spec: AgentSpec, *, week6: Path, memory_parent: Path) -> list[str]:
    seen: list[str] = []
    for t in spec.tools or []:
        x = (t or "").strip().lower().replace(" ", "_").replace("-", "_")
        if x and x not in seen:
            seen.append(x)
    for extra in (
        "fetch",
        "memory",
        "pushover",
        "resend",
        "duckduckgo",
        "playwright",
        "serper",
        "alphavantage",
    ):
        if extra not in seen and build_stdio_params(
            extra, sanitize_name(spec.name), week6=week6, memory_parent=memory_parent
        ):
            seen.append(extra)
    return seen


def all_team_tool_ids(team: TeamSpec, *, week6: Path, memory_parent: Path) -> list[str]:
    u: set[str] = set()
    for spec in [team.manager, *team.specialists]:
        for t in effective_tool_ids(spec, week6=week6, memory_parent=memory_parent):
            u.add(t)
    return sorted(u)


def _server_key_memory(slug: str) -> tuple[str, str]:
    return ("memory", slug)


async def run_generated_team(project_dir: Path, task: str) -> str:
    from agents import Agent, Runner, trace, set_default_openai_client, set_tracing_export_api_key
    from agents.mcp import MCPServerStdio
    from openai import AsyncOpenAI

    spec_path = project_dir / "team_spec.json"
    team = TeamSpec.model_validate_json(spec_path.read_text(encoding="utf-8"))

    week6 = week6_mcp_root(project_dir)
    memory_parent = project_dir / "memory"

    openrouter_client = AsyncOpenAI(
        api_key=os.getenv("OPENROUTER_API_KEY"),
        base_url="https://openrouter.ai/api/v1",
        default_headers={
            "HTTP-Referer": "http://localhost",
            "X-Title": "Generated team manual run",
        },
    )
    set_default_openai_client(openrouter_client)
    if os.getenv("OPENAI_API_KEY"):
        set_tracing_export_api_key(os.getenv("OPENAI_API_KEY"))

    async with AsyncExitStack() as stack:
        servers: dict[str | tuple[str, str], object] = {}

        for tid in all_team_tool_ids(team, week6=week6, memory_parent=memory_parent):
            if tid == "memory":
                continue
            p = build_stdio_params(
                tid, "na", week6=week6, memory_parent=memory_parent
            )
            if p:
                try:
                    servers[tid] = await stack.enter_async_context(
                        MCPServerStdio(
                            params=p,
                            client_session_timeout_seconds=120,
                            name=f"mcp_{tid}",
                        )
                    )
                except Exception as e:
                    print(f"⚠️ Skipping MCP tool {tid!r} (connection failed): {e}")

        for spec in [team.manager, *team.specialists]:
            if "memory" not in effective_tool_ids(
                spec, week6=week6, memory_parent=memory_parent
            ):
                continue
            slug = sanitize_name(spec.name)
            key = _server_key_memory(slug)
            if key in servers:
                continue
            p = build_stdio_params(
                "memory", slug, week6=week6, memory_parent=memory_parent
            )
            if p:
                try:
                    servers[key] = await stack.enter_async_context(
                        MCPServerStdio(
                            params=p,
                            client_session_timeout_seconds=120,
                            name=f"mcp_memory_{slug}",
                        )
                    )
                except Exception as e:
                    print(
                        f"⚠️ Skipping memory MCP for {slug!r} (connection failed): {e}"
                    )

        def mcps_for_spec(spec: AgentSpec) -> list:
            out = []
            for t in effective_tool_ids(spec, week6=week6, memory_parent=memory_parent):
                if t == "memory":
                    k = _server_key_memory(sanitize_name(spec.name))
                    if k in servers:
                        out.append(servers[k])
                elif t in servers:
                    out.append(servers[t])
            return out

        def create_agent(spec: AgentSpec) -> Agent:
            return Agent(
                name=spec.name,
                instructions=spec.instructions,
                model="openai/openai/gpt-oss-120b",
                handoff_description=spec.handoff_description or f"Transfer to {spec.name}",
                mcp_servers=mcps_for_spec(spec),
                mcp_config={"convert_schemas_to_strict": False},
            )

        specialists = [create_agent(s) for s in team.specialists]
        mgr_instructions = team.manager.instructions
        if not specialists:
            mgr_instructions += (
                "\n\nYou have no specialist agents to hand off to. Answer the user's task directly."
            )

        manager = Agent(
            name=team.manager.name,
            instructions=mgr_instructions,
            handoffs=specialists,
            model="openai/openai/gpt-oss-120b",
            mcp_servers=mcps_for_spec(team.manager),
            mcp_config={"convert_schemas_to_strict": False},
        )

        with trace("generated_team_manual_run"):
            result = await Runner.run(manager, task)
        return str(result.final_output)


async def main_async() -> None:
    import sys

    project_dir = Path(__file__).resolve().parent
    task = " ".join(sys.argv[1:]).strip() if len(sys.argv) > 1 else "Introduce the team briefly."
    out = await run_generated_team(project_dir, task)
    print(out)


def main() -> None:
    import asyncio

    asyncio.run(main_async())
