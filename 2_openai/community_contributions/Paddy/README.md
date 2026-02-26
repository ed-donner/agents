# Paddy — Content Research (Streamlit)

A **content management / research** flow built on the deep_research pattern: plan searches → run web search → write a report. Uses **Gemini 2.5 Flash** for planning and writing, and **OpenAI (gpt-4o-mini)** for web search (WebSearchTool).

## Architecture (RAG-style)

Paddy follows a **RAG (Retrieval-Augmented Generation)** pattern: a planner decides *what* to retrieve, a search step *retrieves* external context from the web, and a writer *generates* the final report by augmenting the model with that context.

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                         PADDY — RAG-STYLE CONTENT RESEARCH                       │
└─────────────────────────────────────────────────────────────────────────────────┘

  ┌──────────────┐     Query + Context      ┌──────────────────┐
  │   Streamlit  │  (topic, audience,       │   RETRIEVAL      │
  │   UI (3 Qs)  │   focus)                 │   PLANNING       │
  └──────┬───────┘ ──────────────────────► └────────┬─────────┘
         │                                          │
         │                                          │ WebSearchPlan
         │                                          │ (search terms + reasons)
         │                                          ▼
         │                               ┌──────────────────────┐
         │                               │   RETRIEVAL          │
         │                               │   (Web Search)       │
         │                               │   OpenAI + Tool      │
         │                               └──────────┬───────────┘
         │                                          │
         │                                          │ Retrieved docs
         │                                          │ (parallel searches)
         │                                          ▼
         │                               ┌──────────────────────┐
         │                               │   GENERATION         │
         │                               │   (Augmented prompt) │
         │                               │   Query + Context    │
         │                               │   + Retrieved docs   │
         │                               └──────────┬───────────┘
         │                                          │
         │                                          │ ReportData
         │                                          ▼
         │                               ┌──────────────────────┐
         └───────────────────────────────│   Output             │
                                         │   Summary | Report   │
                                         │   | Follow-ups       │
                                         └──────────────────────┘
                                                   │
                                                   │ (optional loop)
                                                   ▼
                                         ┌──────────────────────┐
                                         │   Follow-up Research │
                                         │   (select → refine   │
                                         │    → re-run RAG)     │
                                         └──────────────────────┘
```

### RAG Components

| Phase        | Component       | Model / Tool          | Role                                      |
|--------------|-----------------|------------------------|-------------------------------------------|
| **Planning** | Planner Agent   | Gemini 2.5 Flash      | Decides *what* to retrieve (search queries)|
| **Retrieval**| Search Agent    | OpenAI + WebSearchTool| Retrieves external docs from the web      |
| **Augment**  | Prompt builder  | —                      | Injects query, audience, focus + retrievals|
| **Generation**| Writer Agent   | Gemini 2.5 Flash      | Produces report from augmented context    |

### Mermaid Diagram

```mermaid
flowchart TB
    subgraph UI["Streamlit UI"]
        Q1[1. Topic/Question]
        Q2[2. Audience]
        Q3[3. Focus]
    end

    subgraph RAG["RAG Pipeline"]
        direction TB
        subgraph Plan["RETRIEVAL PLANNING"]
            PA[Planner Agent<br/>Gemini 2.5 Flash]
        end
        subgraph Retrieve["RETRIEVAL"]
            SA[Search Agent<br/>OpenAI + WebSearchTool]
            WEB[(Web)]
        end
        subgraph Generate["GENERATION"]
            WA[Writer Agent<br/>Gemini 2.5 Flash]
        end
    end

    subgraph Out["Output"]
        R[Summary | Full Report | Follow-ups]
        FU[Follow-up Research Loop]
    end

    Q1 --> PA
    Q2 --> PA
    Q3 --> PA
    PA -->|WebSearchPlan| SA
    SA --> WEB
    WEB -->|retrieved docs| WA
    PA -->|query + context| WA
    WA --> R
    R --> FU
    FU -.->|select & refine| PA
```

## Setup

1. From repo root, ensure the main `agents` env is installed (or use the project’s `uv`/pip).
2. In `.env`: set `GOOGLE_API_KEY` (Gemini) and `OPENAI_API_KEY` (for WebSearchTool).
3. Install Streamlit if needed: `pip install streamlit`.

### Streamlit Cloud

Deploy with **Main file path**: `2_openai/community_contributions/Paddy/app.py`.  
In **Manage app → Settings → Secrets**, add:

```toml
GOOGLE_API_KEY = "your-gemini-api-key"
OPENAI_API_KEY = "your-openai-api-key"
```

## Run

From this folder (or with `PYTHONPATH` including the parent so `config` and agents resolve):

```bash
streamlit run app.py
```

## Flow

1. **3 questions** in the app:
   - What to research (topic/question).
   - Audience (technical, executives, general, etc.).
   - Focus or constraints (e.g. time range, competitor comparison).
2. **Research pipeline**: plan searches → run searches (OpenAI) → write report (Gemini).
3. **Output**: one main report (markdown) shown in the Streamlit UI.

No Gradio; no email step. Report is displayed in-app with simple styling.
