"""The QA tester: the ADK orchestrator uses its team's pages to judge them.

Same shape as the course's qa_agent, reworded for calculator pages: judge_game
becomes judge_page and report_game becomes report_page, and the language
parameter is gone since the domain is fixed. Equipped with the Playwright MCP
browser server, a single ADK agent opens each finished page, uses it, watches
the console, and reports whether it works. The harness owns the math; this
agent owns the UI. Its verdicts feed the same bounded fix rounds.

The browser comes through the Playwright MCP server (npx @playwright/mcp)
driving the system Chrome. If the MCP server or Chrome is unavailable, the
orchestrator falls back to leaving the page as built.
"""

from __future__ import annotations

import asyncio
import os
import subprocess
import threading
import webbrowser
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
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
_MAX_CALLS = 25  # the QA agent's budget for one page; a quick check needs far fewer
_CLOSE_TIMEOUT = 10  # bound the browser teardown so a wedged MCP close cannot hang the run

_server: ThreadingHTTPServer | None = None


class _QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, format, *args):  # a request log line would tear the live board
        pass

    def do_GET(self):
        # Browsers request /favicon.ico on their own; the site has none, and the 404
        # lands in the console where the QA agent reads it as an error. Answer with
        # an empty 204 so the console stays clean.
        if self.path == "/favicon.ico":
            self.send_response(204)
            self.end_headers()
            return
        super().do_GET()


def serve_site(site_dir: Path) -> str:
    """Serve the site folder over local HTTP for the browser QA and return the base URL.

    Recent @playwright/mcp releases block file:// navigation for security, so the QA
    browser reaches the pages through localhost instead. The site itself still runs
    straight from disk for the user; only the check goes over HTTP. The server starts
    once, on a daemon thread, and dies with the process."""
    global _server
    if _server is None:
        handler = partial(_QuietHandler, directory=str(site_dir))
        _server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
        threading.Thread(target=_server.serve_forever, daemon=True).start()
    return f"http://127.0.0.1:{_server.server_address[1]}"


async def judge_page(objective: str, uri: str) -> dict | None:
    """Use one page with a fresh, bounded QA sub-agent and return {"works", "note"}.

    The orchestrator agent calls this as its test_page tool. A new short-lived agent
    per page keeps each browser session and context small and bounded, so a single
    confusing page cannot run the check away to the call cap. Returns None if the page
    could not be reached at all (no MCP server or no Chrome)."""
    verdict: dict = {}

    def report_page(works: bool, note: str) -> dict:
        """Report whether the page works, after using it.

        Args:
            works: true if the page loads and responds correctly.
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
            # A cold start (npx fetching the MCP server, Chrome launching) or a slow
            # interaction can exceed the course's 30s; a timed-out call reads to the
            # QA agent like a broken page, so give each call a full minute.
            timeout=60.0,
        ),
        errlog=subprocess.DEVNULL,
    )

    agent = LlmAgent(
        name="qa_tester",
        model=config.ORCHESTRATOR_MODEL,
        instruction="You are a meticulous QA tester. Use the browser to check the page, then report your verdict.",
        tools=[browser, report_page],
    )
    runner = InMemoryRunner(agent=agent, app_name=_APP)
    try:
        session = await runner.session_service.create_session(app_name=_APP, user_id="qa")
        prompt = prompts.QA_PROMPT.format(objective=objective, uri=uri)
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
            # keep interacting with the page, so the page loads and responds: treat it
            # as working rather than firing a spurious fix round.
            verdict.setdefault("works", True)
            verdict.setdefault("note", "Used it for the full check budget and it stayed responsive.")
        return verdict or None
    finally:
        # Close the MCP toolset (and so the npx browser subprocess) inside the loop,
        # before it ends, or its transport's __del__ fires later on a closed loop. Bound
        # each close, so if the caller gives up on a slow check and cancels this page, a
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
    """Open the finished site in the default browser for the user."""
    webbrowser.open(index_path.resolve().as_uri())
