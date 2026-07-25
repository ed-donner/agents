from __future__ import annotations

import asyncio
import contextlib
import os
import socket
import subprocess
import random
import time
from pathlib import Path

from dotenv import load_dotenv
from openai import AsyncOpenAI

from agents import Agent, Runner, set_default_openai_api, set_default_openai_client, set_tracing_disabled
from agents.mcp import MCPServerSse, MCPServerStdio

cities = ["Tokyo", "Lagos", "Berlin", "São Paulo", "Toronto", "Cairo", "Sydney", "Mumbai", "Seoul", "Nairobi"]
topics = [
    ("stdio transport", "stdio mode connects MCP servers via standard input/output, ideal for local processes."),
    ("SSE transport", "SSE mode uses HTTP streaming to connect remote MCP servers over a network."),
    ("MCP tool calls", "MCP tool calls allow agents to invoke server-side functions with structured arguments."),
    ("LibSQL memory", "LibSQL stores persistent agent memory in a local SQLite file for fast retrieval."),
    ("MCP vs REST", "MCP differs from REST by maintaining a stateful session between client and server."),
]
echo_messages = ["ping", "test-run", "hello-agent", "status-check", "mcp-alive"]

SCRIPT_DIR = Path(__file__).resolve().parent
# najeeb_mcp -> community_contributions -> 6_mcp -> repo root
REPO_ROOT = SCRIPT_DIR.parents[2]
SSE_PORT = int(os.environ.get("SERVER_MCP_SSE_PORT", "8765"))
SSE_HOST = os.environ.get("SERVER_MCP_SSE_HOST", "127.0.0.1")
SSE_URL = f"http://{SSE_HOST}:{SSE_PORT}/sse"


def _wait_for_port(host: str, port: int, timeout: float = 20.0) -> None:
    timer = time.monotonic() + timeout
    while time.monotonic() < timer:
        try:
            with socket.create_connection((host, port), timeout=1.0):
                return
        except OSError:
            time.sleep(0.2)
    raise TimeoutError(f"Nothing listening on {host}:{port} after {timeout}s")


def _stdio_params(script: str) -> dict:
    return {
        "command": "uv",
        "args": ["run", "python", str(SCRIPT_DIR / script)],
        "cwd": str(REPO_ROOT),
    }


async def _run() -> None:
    load_dotenv(override=True)
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("API key not found")
        return

    base_url = "https://openrouter.ai/api/v1"
    model = "openai/gpt-4o-mini"

    set_default_openai_api("chat_completions")
    set_tracing_disabled(True)
    set_default_openai_client(
        AsyncOpenAI(base_url=base_url, api_key=api_key),
        use_for_tracing=False,
    )

    proc: subprocess.Popen[str] | None = None
    try:
        proc = subprocess.Popen(
            [
                "uv",
                "run",
                "python",
                str(SCRIPT_DIR / "remote_sse_server.py"),
            ],
            cwd=str(REPO_ROOT),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        _wait_for_port(SSE_HOST, SSE_PORT)

        notes = MCPServerStdio(
            name="local_notes",
            params=_stdio_params("notes_server.py"),
            client_session_timeout_seconds=60,
        )
        weather = MCPServerStdio(
            name="open_meteo",
            params=_stdio_params("weather_server.py"),
            client_session_timeout_seconds=60,
        )
        remote = MCPServerSse(
            name="remote_sse",
            params={
                "url": SSE_URL,
                "timeout": 30,
                "sse_read_timeout": 300,
            },
            client_session_timeout_seconds=120,
        )

        city = random.choice(cities)
        note_title, note_body = random.choice(topics)
        echo_msg = random.choice(echo_messages)

        instructions = (
            f"You have three MCP servers. "
            f"1) Local notes: call save_local_note with title='{note_title}' and body='{note_body}' "
            f"Then call list_local_notes and report how many notes are stored. "
            f"2) Weather: call weather_for_city for '{city}' and include the temperature, condition, "
            f"and a one-sentence observation about the weather. "
            f"3) Remote SSE: call remote_utc_now and remote_echo with message='{echo_msg}'. "
            f"Reply with a short markdown summary of outputs from each group, "
            f"using a heading for each server and bullet points for the results."
        )

        agent = Agent(
            name="TriModeMCP",
            instructions=instructions,
            model=model,
            mcp_servers=[notes, weather, remote],
        )

        async with notes, weather, remote:
            result = await Runner.run(agent, "Execute the instruction once; be concise.")
            print(result.final_output)
    finally:
        if proc is not None:
            proc.terminate()
            with contextlib.suppress(subprocess.TimeoutExpired):
                proc.wait(timeout=5)
            if proc.poll() is None:
                proc.kill()


def main() -> None:
    asyncio.run(_run())


if __name__ == "__main__":
    main()
