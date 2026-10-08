"""The orchestrator: a Google ADK agent that runs the Mission Control team as a loop.

Same shape as the course's Day 5 orchestrator, with three changes for the scoring
loop. Each framework's assignment is fixed (prompts.CALC_SPECS), because the
harness checks exact function signatures. A score_site tool runs the deterministic
physics harness and reports every failing check. And the course's single fix round
becomes a per-builder round counter, so the agent can keep sending a builder back
until its module passes or its rounds run out.

The whole run lives on one event loop. The launch and wait tools spawn workers with
plain subprocess.Popen (no asyncio transports to outlive the loop), and the browser
QA closes its MCP toolset in-loop, so there is no "event loop is closed" teardown.
"""

from __future__ import annotations

import asyncio
import os
import re
import signal
import subprocess
import sys
import time
from pathlib import Path

from quiet import silence

silence()

from google.adk.agents import LlmAgent  # noqa: E402
from google.adk.agents.invocation_context import LlmCallsLimitExceededError  # noqa: E402
from google.adk.agents.run_config import RunConfig  # noqa: E402
from google.adk.runners import InMemoryRunner  # noqa: E402
from google.genai import types  # noqa: E402
from rich.live import Live  # noqa: E402

import board  # noqa: E402
import catalog  # noqa: E402
import config  # noqa: E402
import css_agent  # noqa: E402
import live_board  # noqa: E402
import prompts  # noqa: E402
import qa_agent  # noqa: E402
import scoring  # noqa: E402

_APP = "agent_loop"
_MAX_TURNS = 120  # bounds the outer loop; higher than the course's 80 because the scoring loop adds rounds
CALC_FILES = ("calc.html", "calc.css", "calc.js", "logic.js")
WORKER_TIMEOUT = int(os.environ.get("WORKER_TIMEOUT_S", "300"))  # a worker hung past this is stopped so the run never stalls
QA_TIMEOUT = int(os.environ.get("QA_TIMEOUT_S", "150"))  # a browser QA wedged past this is given up on so the run never stalls
SCORE_TARGET = int(os.environ.get("SCORE_TARGET", "90"))  # the harness score the agent iterates towards, in percent
MAX_FIX_ROUNDS = int(os.environ.get("MAX_FIX_ROUNDS", "3"))  # fix rounds per builder before its module is left as is
_TITLE_RE = re.compile(r"<title[^>]*>(.*?)</title>", re.IGNORECASE | re.DOTALL)


def _read_title(calc_html: Path) -> str:
    """The title the builder gave its page, read from calc.html (empty if not found)."""
    try:
        match = _TITLE_RE.search(calc_html.read_text(encoding="utf-8"))
    except OSError:
        return ""
    return match.group(1).strip() if match else ""


def is_built(folder: Path) -> bool:
    """True if all four calculator files exist in the folder and are non-empty."""
    return all((folder / f).exists() and (folder / f).stat().st_size for f in CALC_FILES)


def _launch(goal_id: int, worker: dict, board_path: Path) -> subprocess.Popen:
    """Start one worker as a subprocess against the shared board.

    stdout and stderr go to DEVNULL: a worker's framework banner would otherwise tear
    the live board, and the worker only ever talks to us through the board. On POSIX,
    start_new_session puts the worker and its uv/npx/MCP tree in their own session so a
    timeout can stop the whole tree at once; on Windows the same job is done by
    taskkill /T in _terminate, so no new group is needed at launch.
    """
    argv = catalog.launch_argv(worker, goal_id, board_path)
    cwd = str((catalog.HERE / worker["file"]).resolve().parent)
    group = {} if sys.platform == "win32" else {"start_new_session": True}
    return subprocess.Popen(
        argv, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, cwd=cwd, **group
    )


def _terminate(proc: subprocess.Popen) -> None:
    """Stop a worker and its uv/npx/MCP child tree (used only when a worker overruns its
    timeout). On Windows taskkill /T kills the whole tree by pid; on POSIX a SIGTERM to
    the process group does the same."""
    try:
        if sys.platform == "win32":
            subprocess.run(
                ["taskkill", "/F", "/T", "/PID", str(proc.pid)],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        else:
            os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
    except (ProcessLookupError, OSError):
        pass


class Team:
    """The orchestrator's working state: the discovered workers and what has been
    launched so far. The tools read and mutate this; the agent never sees it."""

    def __init__(self, workers: list[dict], site_dir: Path, board_path: Path) -> None:
        self.workers = workers
        self.site_dir = site_dir
        self.board_path = board_path
        self.by_key = {w["key"]: w for w in workers}
        self.by_slug = {w["slug"]: w for w in workers}
        self.launched: set[str] = set()  # slugs whose builder has been started
        self.registry: dict[int, dict] = {}  # goal id -> worker (with its objective), colours the live board
        self.pending: list[subprocess.Popen] = []  # launched but not yet waited for
        self.rounds: dict[str, int] = {}  # slug -> fix rounds used, capped at MAX_FIX_ROUNDS
        self.last_score: dict | None = None  # the most recent harness result, for the hub badge
        self.qa_notice_shown = False  # the hands-off notice for the viewer, printed once

    def _built(self, slug: str) -> bool:
        return is_built(self.site_dir / slug)

    def _short(self, slug: str) -> str:
        return prompts.CALC_SPECS[slug]["short"]

    def status(self) -> str:
        lines = []
        for w in self.workers:
            slug = w["slug"]
            lines.append(f"  {w['name']} ({self._short(slug)}) [{slug}/]: {'built' if self._built(slug) else 'NOT built'}")
        return "Team status:\n" + "\n".join(lines)

    def finished_pages(self) -> list[dict]:
        """The built calculators as [{label, slug}], each labelled by the title its
        builder gave it."""
        pages = []
        for worker in self.workers:
            slug = worker["slug"]
            if not self._built(slug):
                continue
            label = _read_title(self.site_dir / slug / "calc.html") or self._short(slug) or worker["name"]
            pages.append({"label": label, "slug": slug})
        return pages

    def score_line(self) -> str:
        """The badge text for the hub, from the latest harness result."""
        return scoring.badge(self.last_score) if self.last_score else "score unavailable"


def make_tools(team: Team) -> list:
    """Build the orchestrator agent's tools as closures over the team state."""

    async def author_style() -> str:
        """Author the site's shared house style (common.css). Do this once, before
        the builders start."""
        await css_agent.author_style(team.site_dir)
        return "Authored common.css, the shared house style for the site."

    def launch_worker(framework: str) -> str:
        """Start one framework's builder on its fixed calculator assignment. Returns
        immediately; it works in the background. Start all your builders, then call
        wait_for_team.

        Args:
            framework: the framework key, one of strands, pydantic, maf, agno, mastra.
        """
        worker = team.by_key.get(framework)
        if worker is None:
            return f"No builder named '{framework}'. Your team is: {', '.join(team.by_key)}."
        slug = worker["slug"]
        if slug in team.launched:
            return f"{worker['name']} is already building the {team._short(slug)} calculator."
        team.launched.add(slug)
        spec = prompts.CALC_SPECS[slug]
        (team.site_dir / slug).mkdir(parents=True, exist_ok=True)
        task = prompts.CALC_TASK.format(
            objective=spec["objective"], contract=spec["contract"], names=spec["names"], slug=slug
        )
        goal_id = board.add_goal(task)
        team.registry[goal_id] = {**worker, "objective": spec["short"]}
        team.pending.append(_launch(goal_id, worker, team.board_path))
        return f"Launched {worker['name']} to build the {spec['short']} calculator (folder {slug}/)."

    async def wait_for_team() -> str:
        """Wait until every builder you have started has finished, watching the shared
        board fill in while they work. Returns which pages are now built."""
        procs = team.pending
        team.pending = []
        if not procs:
            return team.status()
        started = time.monotonic()
        stopped = False
        with Live(live_board.render(team.registry), console=live_board.console, refresh_per_second=8) as live:
            while any(p.poll() is None for p in procs):
                live.update(live_board.render(team.registry))
                if not stopped and time.monotonic() - started > WORKER_TIMEOUT:
                    for p in procs:
                        if p.poll() is None:
                            _terminate(p)
                    stopped = True
                await asyncio.sleep(0.15)
            live.update(live_board.render(team.registry))
        return team.status()

    def score_site() -> str:
        """Run the physics test harness against every builder's logic.js and report
        the score with every failing check spelled out. Measure after each wait."""
        result = scoring.run(team.site_dir, [w["slug"] for w in team.workers])
        if result is None:
            return "Could not run the scoring harness (is Node installed?). Skip the scoring loop and continue."
        team.last_score = result
        live_board.console.print(
            f"Score: {result['passed']}/{result['total']} checks nominal ({result['percent']}%)",
            style="bold green" if result["percent"] >= SCORE_TARGET else "bold red",
        )
        report = scoring.format_report(result)
        if result["percent"] >= SCORE_TARGET:
            return f"{report}\n\nThe score meets the {SCORE_TARGET}% target."
        return f"{report}\n\nThe score is below the {SCORE_TARGET}% target; relaunch the failing builders with their failing checks."

    async def test_page(slug: str) -> str:
        """Open one finished calculator page in a real browser and use it to judge
        whether it works. Watch the browser to see the page being used.

        Args:
            slug: the builder's folder name, which is its framework key, e.g. strands.
        """
        worker = team.by_slug.get(slug)
        if worker is None:
            return f"No page in folder '{slug}'. Folders: {', '.join(team.by_slug)}."
        if not team._built(slug):
            missing = [f for f in CALC_FILES if not (team.site_dir / slug / f).exists() or not (team.site_dir / slug / f).stat().st_size]
            return f"{slug} is not built yet (missing or empty: {', '.join(missing)}). Wait for the team, or fix it."
        if not team.qa_notice_shown:
            team.qa_notice_shown = True
            live_board.console.print(
                "Automated browser testing is starting: a Chrome window will open, get used and close "
                "on its own for each page. Please do not click inside it, type in it, or close it.",
                style="bold",
            )
        # The QA browser gets the page over localhost, not file://, because recent
        # Playwright MCP releases block file: navigation. The page itself is unchanged.
        uri = f"{qa_agent.serve_site(team.site_dir)}/{slug}/calc.html"
        live_board.console.print(f"Using {worker['name']}'s page to check it", style=worker["colour"])
        try:
            verdict = await asyncio.wait_for(
                qa_agent.judge_page(prompts.CALC_SPECS[slug]["objective"], uri),
                timeout=QA_TIMEOUT,
            )
        except Exception as exc:
            live_board.console.print(f"  could not finish checking {worker['name']} ({type(exc).__name__})", style="dim")
            return f"Could not finish checking {slug} ({type(exc).__name__}); leave it as built."
        if not verdict:
            live_board.console.print(f"  could not use {worker['name']} (browser unavailable)", style="dim")
            return f"Could not use {slug} (the browser may be unavailable); leave it as built."
        works = bool(verdict.get("works"))
        note = verdict.get("note", "")
        live_board.console.print(f"  {worker['name']}: {'WORKS' if works else 'BROKEN'}. {note}", style="green" if works else "red")
        return f"{slug}: {'WORKS' if works else 'BROKEN'}. {note}"

    def relaunch_worker(framework: str, problem: str) -> str:
        """Send a framework's builder back to fix its calculator. Returns immediately;
        call wait_for_team afterwards. Each builder has a limited number of fix rounds.

        Args:
            framework: the framework key whose calculator has problems.
            problem: what is wrong, e.g. the failing checks copied from the score
                report, or the symptom the browser check found.
        """
        worker = team.by_key.get(framework)
        if worker is None:
            return f"No builder named '{framework}'."
        slug = worker["slug"]
        used = team.rounds.get(slug, 0)
        if used >= MAX_FIX_ROUNDS:
            return f"{worker['name']} has used all {MAX_FIX_ROUNDS} of its fix rounds; leave its calculator as it is."
        team.rounds[slug] = used + 1
        spec = prompts.CALC_SPECS[slug]
        text = prompts.FIX_TASK.format(slug=slug, objective=spec["objective"], symptom=problem)
        goal_id = board.add_goal(text)
        team.registry[goal_id] = {**worker, "objective": spec["short"]}
        team.pending.append(_launch(goal_id, worker, team.board_path))
        return f"Sent {worker['name']} back to fix its calculator (round {used + 1} of {MAX_FIX_ROUNDS}, folder {slug}/)."

    async def build_hub() -> str:
        """Author the themed home page (index.html) with the score badge, linking every
        finished calculator. Call this once, after the scoring loop is done."""
        pages = team.finished_pages()
        if not pages:
            return "No finished calculators to link yet; build some first."
        await css_agent.build_hub(pages, team.score_line(), team.site_dir)
        return (
            f"Authored index.html with the badge '{team.score_line()}', linking "
            f"{len(pages)} calculator(s): {', '.join(p['label'] for p in pages)}."
        )

    return [author_style, launch_worker, wait_for_team, score_site, test_page, relaunch_worker, build_hub]


def _build_agent(team: Team) -> LlmAgent:
    team_lines = "\n".join(
        f"- {w['name']} (framework key: {w['key']}, folder: {w['slug']}/): {prompts.CALC_SPECS[w['slug']]['short']}"
        for w in team.workers
    )
    instruction = prompts.ORCHESTRATOR_PROMPT.format(team=team_lines, target=SCORE_TARGET, rounds=MAX_FIX_ROUNDS)
    return LlmAgent(name="orchestrator", model=config.ORCHESTRATOR_MODEL, instruction=instruction, tools=make_tools(team))


async def _run(team: Team) -> None:
    runner = InMemoryRunner(agent=_build_agent(team), app_name=_APP)
    try:
        session = await runner.session_service.create_session(app_name=_APP, user_id="orchestrator")
        async for event in runner.run_async(
            user_id="orchestrator",
            session_id=session.id,
            new_message=types.UserContent(
                "Build Mission Control with your team: start every builder, measure the site with the "
                "harness, iterate until the score clears the target, check the pages in the browser, "
                "then assemble the home page."
            ),
            run_config=RunConfig(max_llm_calls=_MAX_TURNS),
        ):
            if event.content and event.content.parts:
                for part in event.content.parts:
                    if part.text and part.text.strip():
                        live_board.console.print(part.text.strip(), style="dim italic")
    except LlmCallsLimitExceededError:
        # The orchestrator used its whole turn budget. Stop cleanly and let the safety
        # net below finish the site; the pages it did build are still on disk.
        print(f"\n  NOTE: the orchestrator reached its {_MAX_TURNS}-step budget; wrapping up with what is built.")
    except Exception as exc:
        # A transient model or network error (a DNS blip, a 5xx from the API) on the
        # orchestrator's own call would otherwise crash the whole run with a traceback.
        # The pages are already built on disk, so stop cleanly and let the safety net
        # below finish the hub. The type is printed so a real fault is still visible.
        print(f"\n  NOTE: the orchestrator stopped early after an error ({type(exc).__name__}); wrapping up with what is built.")
    finally:
        try:
            await runner.close()
        except Exception:
            pass


def _ensure_site(team: Team) -> None:
    """A non-LLM safety net so the site always has a look and a front door, even if the
    orchestrator stopped before authoring them. Only fills in what is missing. The badge
    comes from the last harness run, or a fresh one if the agent never scored."""
    if not (team.site_dir / "common.css").exists():
        css_agent.write_template_style(team.site_dir)
    if not (team.site_dir / "index.html").exists():
        if team.last_score is None:
            team.last_score = scoring.run(team.site_dir, [w["slug"] for w in team.workers])
        css_agent.write_template_hub(team.finished_pages(), team.score_line(), team.site_dir)
        print("  NOTE: the orchestrator did not author index.html; wrote the plain template instead.")


def run(workers: list[dict], site_dir: Path, board_path: Path) -> Team:
    """Reset the shared board, then let the orchestrator agent build and score the site."""
    site_dir.mkdir(parents=True, exist_ok=True)
    board.reset_board()
    team = Team(workers, site_dir, board_path)
    asyncio.run(_run(team))
    _ensure_site(team)
    return team
