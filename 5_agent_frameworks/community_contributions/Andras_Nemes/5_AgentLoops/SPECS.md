# Mission Control

Solution to the Week 5 Day 5 exercise (`5_agent_frameworks/5_agent_loop`). Same architecture as the course capstone, applied to a different problem: instead of an arcade of language games, the team builds a set of space travel calculators, and an automatic scoring loop pushes the results until they are correct.

## What is being built

A static website in `site/`: a Mission Control hub page linking five calculator pages, one per agent framework. Each calculator is self-contained vanilla HTML, CSS and JavaScript and runs straight from disk (file://). A shared `common.css` gives the site one look, authored once at the start of the run.

## The team

A Google ADK agent orchestrates. It never writes a calculator itself; it launches the workers, scores the results, and sends builders back to fix failures. The assignments are fixed per framework (in `prompts.py`), because the scoring harness checks exact function signatures. The five workers are the unchanged worker files from Days 2 to 4, launched as subprocesses against one shared SQLite board:

| Framework | Calculator | Ground truth used for scoring |
|---|---|---|
| AWS Strands | Rocket equation (delta-v from Isp and mass ratio) | Tsiolkovsky formula |
| Pydantic AI | Hohmann transfer planner | Earth to Mars: about 259 days |
| Microsoft Agent Framework | Kepler orbital period calculator | Earth at 1 AU: 365.25 days, ISS: about 92 minutes |
| Agno | Launch window finder (synodic periods) | Earth-Mars window: about 780 days |
| Mastra | Escape velocity and surface gravity comparator | Earth: 11.19 km/s, Moon: 2.38 km/s |

## How it works

1. The orchestrator authors `common.css`, the shared house style.
2. It launches all five workers in parallel. Each worker reads its task off the shared board, plans its own steps there, and writes four files into its folder: `calc.html`, `calc.css`, `calc.js` and `logic.js`.
3. `logic.js` is the contract: pure exported functions with exact signatures named in the task text. The page UI is the worker's own invention; the math must live in these functions so it can be scored.
4. A deterministic Node harness (`harness.mjs`, no LLM, no browser) evaluates each `logic.js` in a sandbox and runs 6 known-answer physics checks per module, 30 in total, with tolerances. It reports a total score and the exact failing checks. `scoring.py` runs it and words the report for the agent.
5. The outer feedback loop: the orchestrator calls its `score_site` tool, relaunches any builder whose module has failures, passing it the failing assertion text, waits, and scores again. It iterates until the total score reaches 90% or a builder has used its 3 fix rounds.
6. A Playwright browser QA agent also plays each page to check it loads and responds. The harness owns correctness, the QA agent owns usability; both feed the same relaunch mechanism.
7. The orchestrator authors `index.html`, the hub. The hub shows a score badge with the final harness result (for example "27/30 checks nominal (90%)") and links each calculator by the title its builder gave it.

Progress is visible while it runs: the shared board renders live in the terminal, one colour per worker, with each worker's own steps striking through as they finish, plus the score report between rounds.

## What is reused from the course

`board.py`, `quiet.py`, `live_board.py` and `config.py` are unchanged copies. `catalog.py` only has its relative paths adjusted to reach the worker files from this folder. `prompts.py`, `css_agent.py` and `qa_agent.py` keep their structure with the wording changed for this domain; `prompts.py` adds the fixed per-framework contracts. `orchestrator.py` keeps its shape; the single fix round becomes a per-worker round counter and it gains the `score_site` tool. `harness.mjs` and `scoring.py` are new. The worker files themselves are not copied or modified; they run from their Day 2 to 4 folders.

## How to run it

From a terminal in this folder:

```bash
uv run agent_loop.py                 # build and score the full site
uv run agent_loop.py --skip mastra   # leave a framework out
uv run agent_loop.py --dry-run       # show the plan without running the agent
uv run agent_loop.py --no-open       # do not open the site at the end
```

Requirements are the same as the course's Day 5: `OPENAI_API_KEY` and `GOOGLE_API_KEY` in the repo root `.env`, Node 24 for the Mastra worker and the scoring harness, and Chrome for the browser QA. Models are set in `config.py`. The `SCORE_TARGET` and `MAX_FIX_ROUNDS` environment variables override the 90% target and the 3 fix rounds for a one-off run.

When the run finishes it prints a link to `site/index.html`. Open it, check the score badge, and try the calculators.

## Change log

Modifications made after the first real runs, with the reason for each.

**2026-07-05, after run 1.** The build succeeded (30/30 on the first pass) but every browser QA check and then the orchestrator itself died with `_ResourceExhaustedError`, the Gemini 429 quota error. The orchestrator had fired all five `test_page` calls at once, and five parallel QA agents streaming browser snapshots to `gemini-3.5-flash` exceeded the per-minute quota. The site was left with the plain template hub because the orchestrator never reached `build_hub`.

- Changed the default `ORCHESTRATOR_MODEL` in `config.py` from `gemini-3.5-flash` to `gemini-3.1-flash-lite`, which has more quota headroom. This model runs the orchestrator, the art director and the QA agents.
- One built page (strands) shipped inputs whose own defaults were invalid: `min="0.000001"` anchors the HTML step grid at that offset, so with `step="1"` the default 350 fails browser validation. Extended the task text in `prompts.py` to require defaults that satisfy the inputs' own min, max and step constraints, and to prefer `step="any"`. Also patched the six affected inputs in the already built strands and agno pages.

**2026-07-05, after run 2.** The build again scored 30/30, but four QA agents reported working pages as BROKEN with "the file: protocol is blocked", and the fifth QA check plus the orchestrator again hit `_ResourceExhaustedError`. Recent `@playwright/mcp` releases block `file://` navigation for security, and the project installs `@playwright/mcp@latest`, so the block appeared without any code change here. False BROKEN verdicts are dangerous: they would burn fix rounds on games that are not broken.

- Added `serve_site` to `qa_agent.py`: a small stdlib HTTP server on a daemon thread that serves the site folder on localhost. `test_page` in `orchestrator.py` now hands the QA browser `http://127.0.0.1:<port>/<slug>/calc.html` instead of the `file://` URI. The pages themselves still run straight from disk for the user; only the check goes over HTTP.
- Added one line to the orchestrator prompt in `prompts.py`: test one page at a time and wait for each verdict, never in parallel. This keeps the QA traffic inside the per-minute quota so the run survives to author the themed hub.

**2026-07-05, after run 3.** The run got through the whole flow, but one QA check logged `McpError: Timed out while waiting for response to ClientRequest. Waited 30.0 seconds` and then reported a working page as BROKEN, citing an unresponsive interaction and a favicon 404. Two separate causes. The Playwright MCP connection had a 30 second per-call cap, so a slow call (a cold start or a slow interaction) died mid-check and the QA agent read its own timed-out call as a broken page. And the QA HTTP server had no favicon: browsers request /favicon.ico on their own, the 404 landed in the console, and the QA prompt tells the agent to treat console errors as failures. A false BROKEN verdict burns a fix round on a healthy page.

- Raised the Playwright MCP per-call timeout in `qa_agent.py` from 30 to 60 seconds, so cold starts and slow interactions stop reading as failures.
- The QA HTTP server in `qa_agent.py` now answers /favicon.ico with an empty 204, so the console stays clean at the source.
- Added one sentence to the QA prompt in `prompts.py`: a missing favicon is not an error.
- Added a one-time console notice in `orchestrator.py`, printed before the first browser test: automated testing is ongoing, and the viewer should not click inside, type in, or close the Chrome windows that open during the checks.
