# Welcome to Week 5 - Agent Frameworks

## Day 5: Project 7 - The Agent Loop

All week you built the same worker five times, once in each framework, and watched the idioms rhyme. Today those workers stop working alone and start working as a team, led by an agent.

The orchestrator is itself a Google ADK agent. You give it a goal, build a language arcade with this team, and a handful of tools: author the shared look, kick off each framework's worker, wait for the team, play a finished game in a real browser to check it, and send a builder back to fix one that does not work. Then you let it run. It hands each worker a small game, launches them all at once against a single shared board, paints that board live while five agents write in parallel, authors a themed home page, plays each game to judge it, and reorders any repairs itself. What you get at the end is a little arcade that teaches a language, assembled by five frameworks and run by a sixth.

The inner loop you met four times this week (read the board, plan steps, work them, check them off) is still here. Today it becomes an outer loop, and an agent runs it: the same workers, now coordinated by one that decides who builds, what works, and who to send back.

### How this day works

This day is a program you run, not a notebook. The orchestrator is `agent_loop.py`, and the games it builds are written to a `site/` folder while you watch. Read this file for the story, open the modules it points at to see how the pieces fit, then run it from a terminal and watch the board fill in.

The key idea to hold onto: the five workers are the exact files you already built on Days 2 to 4. You are not writing new workers today. You are letting the ones you have build something together.

## Setup

Almost nothing new: Day 5 runs on the same tools you have used all week.

- **No new Python packages.** It uses the same root `uv` project as Days 1 to 3, and `uv run` keeps that in sync on its own, so there is nothing to install.
- **`OPENAI_API_KEY`** and **`GOOGLE_API_KEY`** in the repo-root `.env`, the same keys you have used all week. The orchestrator and the workers read them with `dotenv`.
- **Node 24** for the one TypeScript worker (Mastra), exactly as on Day 4. If you skipped Day 4, that worker is simply left out (more on that below).
- **Google Chrome**, which the check-the-work step drives through the Playwright MCP server. Most machines already have it, and the MCP server itself comes from `npx` like the filesystem server you have used all week, so there is nothing to install there either.

Run everything below from a terminal in **this folder**, `agents/5_agent_frameworks/5_agent_loop`.

## The shared board, one file this time

Open `board.py`. It is the same board you have used all week, set to use a common board across all Agents.

## The workers are the ones you already built

Open any worker from earlier in the week, say `../2_strands_pydantic/strands_worker.py`. Near the top it reads two optional arguments:

```python
TASK_ID = int(sys.argv[1]) if len(sys.argv) > 2 else None
```

Run it bare and `TASK_ID` is `None`: it seeds its own goal and translates `notes.txt`, the Day 2 demo, unchanged. Give it a task id and a board path and it joins the team instead: it points its board and file tools at the shared site, claims that one task, builds the game the task describes, and exits. The agent, its tools, and its instructions are identical in both modes. That sameness is the whole point of the week, so today leaves it intact and just adds the small branch that chooses a mode.

## The orchestrator

Open `agent_loop.py` and `orchestrator.py`. `agent_loop.py` is the thin entry point: it discovers which workers you built and starts the agent. `orchestrator.py` is the agent and its tools. The agent itself decides the order of play; its goal-focused prompt lives in `prompts.py`. The tools are where the brittle, deterministic work lives, so the agent owns the decisions and the tools own the mechanics:

- **`author_style`** writes the shared `common.css`, the house style every game inherits, fitted to the language you chose. This is the week's flagship doing the design work, and it runs once up front before the builders start. If the call fails, a plain built-in template is written instead, so the site always has a look.
- **`launch_worker(framework, objective)`** gives that framework's builder a learning objective and starts its worker as a subprocess, then returns straight away. The orchestrator invents a distinct objective for each builder and each builder invents its own game for it. The agent calls `launch_worker` once per framework, so all the workers build at the same time. The task text and all the prompts live in `prompts.py`, kept out of the code.
- **`wait_for_team`** blocks until every worker the agent started has exited, painting the shared board live the whole time with `live_board.py`: each game in its own colour, with the steps that worker writes for itself appearing beneath. This is the part to watch. A worker that hangs is given a time limit and then stopped, so the wait always returns.
- **`test_game(slug)`** plays one finished game to judge it. It hands the game to a short-lived QA agent that picks up a browser through the Playwright MCP server (the same browser-over-MCP idea the Sidekick used in Week 4), opens the game, clicks around, watches the console, and reports whether it works. A fresh agent per game keeps each browser session small and focused.
- **`relaunch_worker(framework, problem)`** drops a fix task naming the symptom and relaunches just that one worker. Each game gets at most one fix attempt; a game still broken after its repair is left visible rather than retried forever.
- **`build_hub`** writes the themed `index.html` home page at the end, once the games are built and checked, linking each one by the title its builder gave it. As with the style, a plain template is written if the call fails, so there is always a front door.

Discovery is by file existence (`catalog.py`). If you skipped Day 3 there is no `maf_worker.py`, so those games are simply not built; you end up with however many workers you have, one to five, and you can drop one on purpose with `--skip`. Watching the agent decide to test a game, read the verdict, and send a builder back is the whole lesson in miniature: an agent given a goal and the means to check its own success.

## Run it

```bash
uv run agent_loop.py
```

Watch the board: five games light up in five colours and fill in as the agents work, then the orchestrator plays each one to check it. When it finishes it prints a link to `site/index.html`. Open it and play.

A few flags:

- `uv run agent_loop.py --language French` builds the whole arcade in another language. Any language works; it goes straight into the prompts.
- `uv run agent_loop.py --skip agno mastra` leaves workers out, handy if you did not build every day.
- `uv run agent_loop.py --dry-run` prints the team it would assemble and stops, without running the agent or spending anything.
- `uv run agent_loop.py --no-open` builds the arcade but does not open it in your browser at the end.

## Choosing the models

Open `config.py`. Two lines set the models: one for the ADK orchestrator, one for the workers. The demo uses the larger models for the best-looking result. To run cheaply, swap them for the lighter ones named in the comments. That is the only place models are set.

## What you built this week

Five frameworks, one mental model. You learned each framework's idioms by building the same agent five times, and today you saw why that was worth doing: because the workers were the same shape, they could be handed to a coordinator and put to work together with almost no glue. The board did the coordinating, the frameworks did the building, and an ADK agent ran the show, deciding who builds, judging the results in a browser, and sending builders back. The same inner loop you wrote four times, now run by an agent.
