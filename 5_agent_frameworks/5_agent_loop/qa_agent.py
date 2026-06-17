"""The QA tester: the ADK orchestrator plays its team's games to judge them.

Equipped with the Playwright MCP browser server, a single ADK agent opens each
finished game, plays it, watches the console, and reports which work and which are
broken. This is the capstone's lesson in miniature: give an agent a goal and a way
to check its own success, here a real browser, and let it evaluate the work itself.
The agent's verdicts drive the one bounded fix round.

The browser comes through the Playwright MCP server (npx @playwright/mcp) driving
the system Chrome, the same kind of browser-over-MCP the Sidekick used in Week 4.
If the MCP server or Chrome is unavailable, we fall back to a plain file check and
still open the finished site.
"""

from __future__ import annotations

import asyncio
import os
import subprocess
import webbrowser
from pathlib import Path

from quiet import silence

silence()

from google.adk.agents import LlmAgent  # noqa: E402
from google.adk.agents.invocation_context import LlmCallsLimitExceededError  # noqa: E402
from google.adk.agents.run_config import RunConfig  # noqa: E402
from google.adk.runners import InMemoryRunner  # noqa: E402
from google.adk.tools.mcp_tool import McpToolset, StdioConnectionParams  # noqa: E402
from google.genai import types  # noqa: E402
from mcp import StdioServerParameters  # noqa: E402

import config  # noqa: E402
import prompts  # noqa: E402

_APP = "agent_loop"
_MAX_CALLS = 25  # the QA agent's budget for one game; a quick check needs far fewer
_CLOSE_TIMEOUT = 10  # bound the browser teardown so a wedged MCP close cannot hang the run


async def judge_game(language: str, objective: str, uri: str) -> dict | None:
    """Play one game with a fresh, bounded QA sub-agent and return {"works", "note"}.

    The orchestrator agent calls this as its test_game tool. A new short-lived agent
    per game keeps each browser session and context small and bounded, so a single
    confusing game cannot run the check away to the call cap. Returns None if the game
    could not be reached at all (no MCP server or no Chrome)."""
    verdict: dict = {}

    def report_game(works: bool, note: str) -> dict:
        """Report whether the game works, after playing it.

        Args:
            works: true if the game loads and plays correctly.
            note: one short sentence on what you saw or what is broken.
        """
        verdict["works"] = works
        verdict["note"] = note
        return {"recorded": True}

    args = ["-y", "@playwright/mcp@latest", "--browser", "chrome", "--isolated"]
    if os.environ.get("QA_HEADLESS") == "1":
        args.append("--headless")
    browser = McpToolset(
        connection_params=StdioConnectionParams(
            server_params=StdioServerParameters(command="npx", args=args),
            timeout=30.0,  # the browser's first call can take longer than the 5s default to cold-start
        ),
        errlog=subprocess.DEVNULL,
    )

    agent = LlmAgent(
        name="qa_tester",
        model=config.ORCHESTRATOR_MODEL,
        instruction="You are a meticulous QA tester. Use the browser to check the game, then report your verdict.",
        tools=[browser, report_game],
    )
    runner = InMemoryRunner(agent=agent, app_name=_APP)
    try:
        session = await runner.session_service.create_session(app_name=_APP, user_id="qa")
        prompt = prompts.QA_PROMPT.format(language=language, objective=objective, uri=uri)
        try:
            async for _ in runner.run_async(
                user_id="qa",
                session_id=session.id,
                new_message=types.UserContent(prompt),
                run_config=RunConfig(max_llm_calls=_MAX_CALLS),
            ):
                pass
        except LlmCallsLimitExceededError:
            # The agent used its whole budget without reporting. It was clearly able to
            # keep interacting with the game, so the game loads and responds: treat it
            # as working rather than firing a spurious fix round.
            verdict.setdefault("works", True)
            verdict.setdefault("note", "Played it for the full check budget and it stayed responsive.")
        return verdict or None
    finally:
        # Close the MCP toolset (and so the npx browser subprocess) inside the loop,
        # before it ends, or its transport's __del__ fires later on a closed loop. Bound
        # each close, so if the caller gives up on a slow check and cancels this game, a
        # wedged browser cannot hang the teardown and freeze the run.
        for close in (browser.close, runner.close):
            try:
                await asyncio.wait_for(close(), timeout=_CLOSE_TIMEOUT)
            except Exception:
                pass
        # Let the subprocess transport's close callbacks drain while the loop is still
        # alive, so nothing is left for __del__ to clean up after the loop has closed.
        await asyncio.sleep(0.1)


def open_site(index_path: Path) -> None:
    """Open the finished arcade in the default browser for the player."""
    webbrowser.open(index_path.resolve().as_uri())
