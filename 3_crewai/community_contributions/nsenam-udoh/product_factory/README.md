# Product Factory

Product Factory is a hierarchical CrewAI engineering team that builds a small Python and Gradio product in an isolated workstream. An outer Flow owns workstream sequencing, a design pre-step, and a bounded quality loop; an outer Gradio UI provides builds, feedback, and explicit sandbox resets.

## Setup

Requirements: Python 3.10–3.13, uv, and Docker. The entrypoints configure UTF-8 automatically on Windows. Install dependencies:

```bash
uv sync
```

Copy `.env.example` to `.env` and fill in `OPENAI_API_KEY` and `OPENROUTER_API_KEY` yourself. Never commit `.env`. The manager, test engineer, and quality inspector use `openai/gpt-5.5`; backend and frontend workers use `openrouter/deepseek/deepseek-v4.1-flash`.

The DeepSeek worker was chosen as a lower-cost coding model. Its OpenRouter provider page listed approximately $0.10–0.21 input and $0.40–0.80 output per million tokens when checked during planning: <https://openrouter.ai/deepseek/deepseek-v4.1-flash>. Prices for `google/gemini-4-argon` and `anthropic/claude-fable-5.2` were not verified; no price claims are made for them.

## Login and traces

```bash
crewai login
crewai traces enable
crewai traces status
```

Every crew sets `tracing=True`, and `.env.example` sets `CREWAI_TRACING_ENABLED=true`. CrewAI prints a `View traces` link after a successful trace export. The app reads the current installation's `.crewai/last_run.json` record through CrewAI's `read_last_run()` API and shows **Open trace** when a URL is available. If no URL appears, use the link printed in the terminal.

## Run

Start the default `main` workstream through the same Flow used by the UI:

```bash
crewai run
```

Or pass explicit CLI inputs:

```bash
uv run product_factory_flow --workstream-id main --requirements "Build a notes product"
uv run product_factory_flow --workstream-id main --requirements "Build a notes product" --feedback "Add search"
```

The Flow writes `sandbox/main/design.md`, then runs the hierarchical crew. Workstreams run sequentially. If quality fails, fixes are appended as `## Follow-up feedback (round N)` and the crew reruns against the same files. The loop stops after `MAX_QUALITY_CYCLES` crew cycles (set to 1 in `flow.py`) or immediately on a passing verdict. Existing files are never reset by a continuation.

To explicitly reset before a CLI build:

```bash
uv run product_factory_flow --workstream-id main --reset
```

## Gradio UI

```bash
uv run app.py
```

The single-column UI supports **Run build**, **Continue with feedback**, and **Reset sandbox**. Builds run on a background thread and a timer polls their status. Reset requires the **This deletes sandbox files** confirmation.

## Team and generated-product constraints

The engineering lead is the hierarchical manager and performs the separate tool-free design pre-step. Four specialists implement the backend, build the Gradio frontend and `_validate.py`, write stdlib `unittest` tests, and independently inspect quality. The inspector has read/list/run tools only and returns `QualityVerdict(passed, fixes, evidence)`.

Generated backend and test code may use only the Python standard library. Only generated `app.py` and `_validate.py` may import Gradio. `_validate.py` must import and build the UI without launching it.

## Sandbox safety and reset

Each workstream id must match `^[a-z0-9][a-z0-9_-]{0,39}$` and maps to `sandbox/<workstream_id>/`. Tools reject paths outside that root, use UTF-8, cap reads and process output at 12,000 characters, and cap a single write at 200,000 characters. Tool result caching is disabled because files and process results change.

Python execution uses an ephemeral Docker container with 1 GB memory, 1 CPU, a 256-process limit, and a 300-second timeout. Timed-out containers are force-removed. Network remains enabled so `uv run` can resolve the generated project's dependencies.

Reset is destructive and only available through the explicit UI action or CLI `--reset`. It removes just the selected workstream, recreates it with `uv init --bare --python 3.13`, and installs Gradio with `uv add gradio`.

## Offline tests

```bash
uv run python -m unittest discover tests
```

The tests mock crews and Docker subprocesses; they require neither Docker nor API keys and make no real model API calls.
