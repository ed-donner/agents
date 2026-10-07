# Stock Picker Crew: Gemini + DuckDuckGo + ntfy (free tier only)

The week 3 Stock Picker crew, changed so it runs entirely on **free services with no credit card**:

| Course version | This version | Why |
|---|---|---|
| OpenAI models | **Google Gemini** (`gemini-3.5-flash-lite`) | Free API key from Google AI Studio |
| OpenAI embeddings for memory | **Gemini embeddings** (`gemini-embedding-001`) | Same Gemini key, no OpenAI needed |
| `SerperDevTool` | **DuckDuckGo search** via [`ddgs`](https://pypi.org/project/ddgs/) | No signup, no API key |
| Pushover | **[ntfy.sh](https://ntfy.sh)** push notifications | No account, free phone app |

## What the crew does

Three agents run in sequence, with memory enabled:

1. **Trending Company Finder** searches the news for 2-3 trending companies in a sector → `output/trending_companies.json`
2. **Financial Researcher** researches each company online → `output/research_report.json`
3. **Stock Picker** picks the best one, sends a push notification to your phone, and writes the report → `output/decision.md`

## Setup

1. **Gemini key:** create a free key at [Google AI Studio](https://aistudio.google.com/apikey).
2. **ntfy:** install the **ntfy** app (Android/iOS) and subscribe to a topic name you make up. Topics are public, so pick something hard to guess.
3. Copy `.env.example` to `.env` and fill in both values:

   ```
   GEMINI_API_KEY=your-gemini-key
   NTFY_TOPIC=your-hard-to-guess-topic
   ```

4. Install and run:

   ```bash
   crewai install
   crewai run
   ```

To change the sector, edit `inputs` in `src/stock_picker/main.py`.

## Staying inside the Gemini free tier

The free tier allows about **15 requests per minute per model**. A crew with memory makes a lot of calls, so the first runs failed with `429 RESOURCE_EXHAUSTED`. Two changes fixed it:

- **`max_rpm=12` on the Crew:** CrewAI waits for the next minute instead of failing.
- **Memory uses a different model** (`gemini-3.1-flash-lite`). The quota is counted per model, so memory's own LLM calls no longer use up the agents' quota. `max_rpm` doesn't throttle memory calls, so this split matters.

## Implementation notes

- `pyproject.toml` needs `crewai[tools,google-genai]`. Without the `google-genai` extra, CrewAI fails with `Google Gen AI native provider not available`.
- `memory=True` on its own defaults to OpenAI. `gemini_memory()` in `crew.py` builds a `Memory` that uses Gemini for both the LLM and the embeddings. The `google-vertex` embedder provider uses the Gemini API, not Vertex, when given an `api_key`.
- `tools/search_tool.py` combines DuckDuckGo news and web results. If either search fails, for example because DuckDuckGo rate-limits it, the error goes back to the agent as text instead of crashing the crew.
- `tools/push_tool.py` sends a plain HTTP POST to `https://ntfy.sh/<NTFY_TOPIC>`.

Contributed by Paresh Tahiliani.
