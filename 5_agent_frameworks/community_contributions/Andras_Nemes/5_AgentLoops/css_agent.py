"""The art director: the orchestrator's tools for the creative, page-authoring work.

Same shape as the course's css_agent. Two jobs, each a single ADK LlmAgent turn:
author_style writes the shared look (common.css) up front; build_hub writes the
themed home page (index.html) at the end, now with a score badge carrying the
harness result. If a call fails or comes back empty, a plain built-in template is
written instead, so the site is never left without a look or a front door.
"""

from __future__ import annotations

from quiet import silence

silence()

from google.adk.agents import LlmAgent  # noqa: E402
from google.adk.runners import InMemoryRunner  # noqa: E402
from google.genai import types  # noqa: E402

import config  # noqa: E402
import prompts  # noqa: E402

_APP = "agent_loop"


async def author_style(site_dir) -> None:
    """Write the shared common.css, authored by ADK, templated on failure.

    Async so the orchestrator agent can call it as a tool on its own event loop,
    rather than spinning up a second one.
    """
    site_dir.mkdir(parents=True, exist_ok=True)
    css = await _safe(prompts.CSS_PROMPT)
    css_ok = len(css) > 40
    (site_dir / "common.css").write_text(css if css_ok else _template_css(), encoding="utf-8")
    if not css_ok:
        print(
            f"  NOTE: {config.ORCHESTRATOR_MODEL} did not author common.css (it may be rate limited or "
            "over a spend cap); used the plain built-in template instead."
        )


async def build_hub(games: list[dict], score_line: str, site_dir) -> None:
    """Write the themed index.html linking each finished calculator, templated on failure.

    games is a list of {"label", "slug"}: the title to show and the folder to link.
    score_line is the badge text with the harness result.
    """
    site_dir.mkdir(parents=True, exist_ok=True)
    links = "; ".join(f'"{g["label"]}" at {g["slug"]}/calc.html' for g in games)
    hub = await _safe(prompts.HUB_PROMPT.format(links=links, score=score_line))
    hub_ok = "<" in hub and len(hub) > 80
    (site_dir / "index.html").write_text(hub if hub_ok else _template_hub(games, score_line), encoding="utf-8")
    if not hub_ok:
        print(
            f"  NOTE: {config.ORCHESTRATOR_MODEL} did not author index.html (it may be rate limited or "
            "over a spend cap); used the plain built-in template instead."
        )


async def _safe(prompt: str) -> str:
    try:
        return await _ask(prompt)
    except Exception:
        return ""


async def _ask(prompt: str) -> str:
    """Run one stateless ADK agent turn and return its text, stripped of code fences."""
    agent = LlmAgent(
        name="art_director",
        model=config.ORCHESTRATOR_MODEL,
        instruction="You are a precise front-end designer. Return only the file contents asked for.",
    )
    runner = InMemoryRunner(agent=agent, app_name=_APP)
    try:
        session = await runner.session_service.create_session(app_name=_APP, user_id="orchestrator")
        parts: list[str] = []
        async for event in runner.run_async(
            user_id="orchestrator", session_id=session.id, new_message=types.UserContent(prompt)
        ):
            if event.content and event.content.parts:
                parts.extend(p.text for p in event.content.parts if p.text)
        return _strip_fences("".join(parts))
    finally:
        # Close the runner inside the loop. google-genai's client teardown otherwise
        # raises a harmless AttributeError on aclose during GC; closing here and
        # letting that quirk go quietly keeps the console clean.
        try:
            await runner.close()
        except Exception:
            pass


def write_template_style(site_dir) -> None:
    """Write the built-in common.css without an LLM call (a safety net for the run)."""
    site_dir.mkdir(parents=True, exist_ok=True)
    (site_dir / "common.css").write_text(_template_css(), encoding="utf-8")


def write_template_hub(games: list[dict], score_line: str, site_dir) -> None:
    """Write the built-in index.html without an LLM call (a safety net for the run)."""
    site_dir.mkdir(parents=True, exist_ok=True)
    (site_dir / "index.html").write_text(_template_hub(games, score_line), encoding="utf-8")


def _strip_fences(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        lines = lines[1:]  # drop the opening ```lang line
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        text = "\n".join(lines).strip()
    return text


def _template_css() -> str:
    return (
        ":root{--bg:#0b0e14;--panel:#141a24;--fg:#e6edf3;--muted:#8b98ad;--accent:#ffb454;"
        "--good:#54d18c;--bad:#f7768e;}\n"
        "*{box-sizing:border-box}body{margin:0;font-family:system-ui,sans-serif;background:var(--bg);"
        "color:var(--fg);line-height:1.5}a{color:var(--accent)}\n"
        ".card{background:var(--panel);border-radius:14px;padding:1.2rem 1.4rem;margin:.6rem 0}\n"
        "button{font:inherit;border:0;border-radius:10px;padding:.6rem 1rem;background:var(--accent);"
        "color:#0b0e14;cursor:pointer}\n"
        "input{font:inherit;background:var(--bg);color:var(--fg);border:1px solid var(--muted);"
        "border-radius:8px;padding:.4rem .6rem}\n"
        ".readout{font-family:ui-monospace,monospace;font-size:1.6rem;color:var(--accent)}\n"
        ".correct{color:var(--good)}.wrong{color:var(--bad)}\n"
    )


def _template_hub(games: list[dict], score_line: str) -> str:
    links = "\n".join(
        f'    <li class="card"><a href="{g["slug"]}/calc.html">{g["label"]}</a></li>'
        for g in games
    )
    return (
        '<!DOCTYPE html>\n<html lang="en">\n<head>\n  <meta charset="UTF-8" />\n'
        '  <meta name="viewport" content="width=device-width, initial-scale=1.0" />\n'
        "  <title>Mission Control</title>\n  <link rel=\"stylesheet\" href=\"common.css\" />\n"
        "</head>\n<body>\n  <main style=\"max-width:640px;margin:3rem auto;padding:0 1rem\">\n"
        "    <h1>Mission Control</h1>\n"
        f'    <p class="card">Systems check: {score_line}</p>\n'
        "    <p>Calculators for planning space travel, built by a team of agents. Pick one:</p>\n"
        f'    <ul style="list-style:none;padding:0">\n{links}\n    </ul>\n  </main>\n</body>\n</html>\n'
    )
