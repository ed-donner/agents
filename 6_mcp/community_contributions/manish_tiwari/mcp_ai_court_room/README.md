# AI Courtroom Debate Simulator

Production-style demo: an MCP server exposes legal search tools; LangChain chat models power four agents (case research, two advocates, judge); Gradio streams a three-round debate with a final judgement. You can **paste your own case** or leave the box empty to **search the web** for a recent matter—the default search query includes **today’s date** for recency.

## Prerequisites

- Python 3.11+
- At least one LLM backend configured (OpenAI, Anthropic, DeepSeek, or local Ollama)
- For best case retrieval: `TAVILY_API_KEY` and/or `SERPAPI_API_KEY` (or `SERPER_API_KEY`) and/or `NEWS_API_KEY`. DuckDuckGo is used as a no-key fallback.

## Setup

```bash
cd /path/to/mcp
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your keys and LLM_PROVIDER / LLM_MODEL
```

## Run

```bash
python app.py
```

Open the printed URL (default `http://127.0.0.1:7860`) and click **Begin trial (async stream)**. The app spawns the MCP stdio server (`mcp_server/server.py`) automatically for case research.

## LLM configuration

Global defaults:

- `LLM_PROVIDER`: `openai` | `claude` | `deepseek` | `ollama`
- `LLM_MODEL`: provider-specific model id

**Multiple providers in one session:** set optional per-role variables, for example:

- `LLM_PROVIDER_PRO` / `LLM_MODEL_PRO`
- `LLM_PROVIDER_AGAINST` / `LLM_MODEL_AGAINST`
- `LLM_PROVIDER_JUDGE` / `LLM_MODEL_JUDGE`
- `LLM_PROVIDER_RESEARCH` / `LLM_MODEL_RESEARCH`

Programmatic facade (optional):

```python
from llm.llm_router import LLMRouter
LLMRouter(model="claude")   # preset alias
```

If the primary model fails to construct, the router falls back to Ollama (`OLLAMA_FALLBACK_MODEL`).

## MCP tools

| Tool | Purpose |
|------|---------|
| `search_case` | Aggregates Tavily, SerpAPI, News API, DuckDuckGo for a legal query (default uses today’s date in the query). |
| `fetch_case_summary` | Second-pass context for a headline or citation fragment. |

Run the server standalone (stdio):

```bash
python mcp_server/server.py
```

## OpenAI Agents SDK note

The PyPI package `openai-agents` installs a top-level Python module named `agents`, which would collide with this project’s `agents/` package when you run `python app.py` from this folder. GPT-class models are therefore wired through **LangChain’s `ChatOpenAI`**, which uses the official **`openai`** Python SDK under the hood—same API credentials, production-grade stack, no import clash.

## Architecture

- `agents/` — case research (MCP), pro/against counsel, judge
- `tools/` — search implementations used by the MCP layer
- `mcp_server/server.py` — FastMCP stdio server
- `core/debate_engine.py` — three rounds: pro → against → judge observation
- `llm/llm_router.py` — OpenAI, Claude, DeepSeek, Ollama via LangChain
- `ui/gradio_ui.py` — streamed dashboard

## Deploying to Hugging Face Spaces

Yes. This app is a **Gradio** UI and can run on a [Gradio Space](https://huggingface.co/docs/hub/spaces-sdks-gradio).

### Steps

1. **Create a Space** on [huggingface.co/new-space](https://huggingface.co/new-space): pick a name, license, visibility, SDK **Gradio**, hardware **CPU basic** (or GPU if you pay and need it).

2. **Upload this project** so the Space repo root matches this folder (`mcp/`): you need `app.py`, `requirements.txt`, and the packages `agents/`, `core/`, `llm/`, `mcp_server/`, `tools/`, `ui/` (same layout as local). You can `git clone` your Space, copy files in, commit, and push.

3. **Entry point:** Spaces run `python app.py` from the repo root. `launch_ui()` detects **`SPACE_ID`** (set automatically on HF) and binds **`0.0.0.0:7860`** so the Space proxy can reach Gradio.

4. **Secrets (required):** In the Space → **Settings** → **Variables and secrets**, add at least:
   - `OPENAI_API_KEY` or `ANTHROPIC_API_KEY` or `DEEPSEEK_API_KEY` (match `LLM_PROVIDER` / `LLM_MODEL` if you set them)
   - Optional but recommended: `TAVILY_API_KEY`, `SERPAPI_API_KEY` or `SERPER_API_KEY`, `NEWS_API_KEY`  
   Do **not** commit `.env` with real keys.

5. **Optional env vars** (same Settings UI): `LLM_PROVIDER`, `LLM_MODEL`, per-role `LLM_PROVIDER_PRO`, etc.

6. **Limitations on Spaces**
   - **Ollama** is not practical on the default CPU Space (no local daemon). Prefer cloud LLM APIs.
   - **Cold start:** first request after sleep may take a while.
   - **MCP subprocess:** `mcp_server/server.py` is spawned with `sys.executable`; this is supported on Linux containers used by Spaces.
   - **Outbound network** is allowed for Tavily, SerpAPI, news, and LLM APIs.

7. **Rebuild:** After changing `requirements.txt` or secrets, trigger a Space rebuild (new commit or “Restart” in Settings).

### “Collision on variables and secrets names”

Each name must appear **at most once** across **Variables** and **Secrets**. You cannot have both a variable and a secret called `OPENAI_API_KEY`. Remove duplicates; keep API keys as **Secrets** only.

Use these **exact** secret names for this project: `OPENAI_API_KEY`, `TAVILY_API_KEY`, `SERPER_API_KEY` (or `SERPAPI_API_KEY`).

If the Space **README** still shows placeholders like `{{title}}` or `{{sdkVersion}}`, replace them with real values (or copy the YAML header from this repo’s deployed `README.md`). Mustache templates are not valid configuration.

### README metadata (optional)

You can add a YAML header at the top of the Space `README.md` so the UI shows the right app:

```yaml
---
title: AI Courtroom Debate Simulator
emoji: ⚖️
colorFrom: blue
colorTo: indigo
sdk: gradio
sdk_version: 5.49.1
app_file: app.py
---
```

Adjust `sdk_version` to match the Gradio version in your `requirements.txt`.

## Disclaimer

This is an **educational simulation**, not legal advice. Case text comes from automated search; verify all citations with primary sources.
