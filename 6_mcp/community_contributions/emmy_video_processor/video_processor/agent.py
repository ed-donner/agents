"""Orchestrate the MCP video tools via the OpenAI Agents SDK."""

from __future__ import annotations

import json
import os
import sys
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, AsyncIterator, List, Optional, Tuple

from agents import Agent, Runner
from agents.exceptions import AgentsException
from agents.items import RunItem, ToolCallItem, ToolCallOutputItem
from agents.mcp import MCPServerStdio

from .mcp_tools import get_video_metadata

MAX_TURNS = 5
PROJECT_ROOT = Path(__file__).resolve().parents[1]
MCP_ENTRYPOINT = "mcp_server"


@asynccontextmanager
async def launch_mcp_server() -> AsyncIterator[MCPServerStdio]:
    """Launch the FastMCP server via stdio and ensure it is cleaned up."""

    params = {
        "command": sys.executable,
        "args": ["-m", MCP_ENTRYPOINT],
        "cwd": str(PROJECT_ROOT),
        "env": os.environ.copy(),
    }
    server = MCPServerStdio(params, cache_tools_list=True, name="video-tools-mcp")
    await server.connect()
    try:
        yield server
    finally:
        await server.cleanup()


async def process_request(
    video_path: str,
    user_request: str,
    model: str,
) -> Tuple[str, Optional[List[str]]]:
    if not video_path:
        return "Please upload a video first!", None

    video_info = await get_video_metadata(video_path)
    instructions = _build_instructions(video_path, video_info, user_request)

    try:
        async with launch_mcp_server() as server:
            agent = Agent(
                name="Video Processor",
                instructions=instructions,
                model=model,
                mcp_servers=[server],
            )
            run_result = await Runner.run(agent, user_request, max_turns=MAX_TURNS)
    except AgentsException as exc:
        return f"❌ Agent run failed: {exc}", None
    except Exception as exc:  # pragma: no cover - defensive logging
        return f"❌ Error processing request: {exc}", None

    operations_log = _build_operations_log(run_result.new_items)
    output_files = _extract_file_outputs(run_result.new_items)

    final_text = (
        str(run_result.final_output)
        if run_result.final_output is not None
        else "Agent completed without a final summary."
    )
    steps_summary = (
        f"\n\n🔧 Steps executed: {' → '.join(operations_log)}"
        if operations_log
        else ""
    )

    return f"✅ {final_text}{steps_summary}", (output_files or None)


def _build_instructions(video_path: str, video_info: dict[str, Any], user_request: str) -> str:
    state = _format_video_state(video_path, video_info)
    return f"""You are an autonomous video processing agent powered by a FastMCP server.
{state}

USER GOAL: {user_request}

IMPORTANT RULES:
1. ALWAYS operate on this exact video_path: {video_path}
2. Call the MCP tools as many times as needed. They already wrap FFmpeg safely.
3. Update your mental model of the current video after each tool completes.
4. For platform requests (Instagram, YouTube, Twitter, Email, WhatsApp) make sure
   the output meets the documented constraints before you stop.
5. Only finish once the user's goal is satisfied and you've confirmed any size/format targets.

AVAILABLE TOOLS ARE PROVIDED BY THE CONNECTED MCP SERVER.
Use them whenever you need to inspect, transform, or export media."""


def _format_video_state(video_path: str, video_info: dict[str, Any]) -> str:
    return """CURRENT VIDEO STATE:
- File: {name}
- Duration: {duration}
- Size: {size}MB
- Resolution: {width}x{height}
- Format: {fmt}
""".format(
        name=Path(video_path).name,
        duration=video_info.get("duration_formatted", video_info.get("duration", "unknown")),
        size=video_info.get("size_mb", "unknown"),
        width=video_info.get("width", "?"),
        height=video_info.get("height", "?"),
        fmt=video_info.get("format", "unknown"),
    )


def _build_operations_log(items: List[RunItem]) -> List[str]:
    log: List[str] = []
    for item in items:
        if isinstance(item, ToolCallItem):
            tool_name = getattr(item.raw_item, "name", None)
            if tool_name:
                log.append(f"✓ {tool_name}")
    return log


def _extract_file_outputs(items: List[RunItem]) -> List[str]:
    paths: List[str] = []
    seen: set[str] = set()

    for item in items:
        if not isinstance(item, ToolCallOutputItem):
            continue

        for candidate in _gather_paths(item.output):
            if candidate not in seen:
                seen.add(candidate)
                paths.append(candidate)

        raw_output = _extract_raw_output(item.raw_item)
        for candidate in _gather_paths(raw_output):
            if candidate not in seen:
                seen.add(candidate)
                paths.append(candidate)

    return paths


def _extract_raw_output(raw_item: Any) -> Any:
    if raw_item is None:
        return None
    if isinstance(raw_item, dict):
        return raw_item.get("output")
    return getattr(raw_item, "output", None)


def _gather_paths(value: Any) -> List[str]:
    found: List[str] = []
    stack: List[Any] = [value]

    while stack:
        current = stack.pop()
        if current is None:
            continue

        if isinstance(current, str):
            normalized = _normalize_path_candidate(current)
            if normalized:
                found.append(normalized)
                continue

            parsed = _try_parse_json(current)
            if parsed is not None:
                stack.append(parsed)
            continue

        if isinstance(current, dict):
            for key, val in current.items():
                if isinstance(val, str) and key.lower().endswith("path"):
                    normalized = _normalize_path_candidate(val)
                    if normalized:
                        found.append(normalized)
                stack.append(val)
            continue

        if isinstance(current, (list, tuple)):
            stack.extend(current)

    return found


def _normalize_path_candidate(value: str) -> Optional[str]:
    stripped = value.strip().strip('"\'')
    if not stripped:
        return None

    candidate_path = Path(stripped).expanduser()
    if not candidate_path.is_absolute():
        candidate_path = (PROJECT_ROOT / candidate_path).resolve()
    else:
        candidate_path = candidate_path.resolve()

    path_str = str(candidate_path)
    return path_str if os.path.exists(path_str) else None


def _try_parse_json(value: str) -> Any:
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return None


__all__ = ["process_request"]
