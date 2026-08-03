# AI Homepage Generator

A multi-agent system powered by LangGraph that generates complete, production-ready HTML homepages from natural language descriptions. Three specialized AI agents collaborate iteratively until the output meets quality standards.

## GOAL

Provide a natural language description of your dream homepage, and the system will design, build, and validate a complete HTML/CSS/JS page — ready to use.

Users can review the output and provide feedback for iterative improvements, with the pipeline automatically re-planning and refining until the result passes validation.

## HOW IT WORKS

The pipeline uses a **LangGraph state machine** with three specialized agents and a validation feedback loop:

```
User Prompt
    │
    ▼
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  Planner Agent  │ ──▶ │ Developer Agent  │ ──▶ │ Validator Agent │
│   (GPT-5 Nano)  │     │  (Gemini 3.1)    │     │  (Claude Sonnet)│
└─────────────────┘     └──────────────────┘     └────────┬────────┘
        ▲                                                   │
        │            ◄── Loop if issues found ──────────────┘
        │
    (max 3 iterations)
```

### Agent Roles

| Agent | Model | Responsibility |
|-------|-------|----------------|
| **Planner** | GPT-5 Nano | Generates structured design guidelines: brand identity, layout, content strategy, style keywords, and technical constraints |
| **Developer** | Gemini 3.1 Flash Lite | Takes guidelines and produces a complete, self-contained HTML/CSS/JS homepage with responsive design |
| **Validator** | Claude Sonnet 4 | Runs 3 parallel checks and decides whether to approve or trigger re-planning |

### Validation Checks (run in parallel)

1. **HTML Quality** — Static analysis with BeautifulSoup (semantic tags, accessibility, structure)
2. **Guideline Conformance** — LLM review checking alignment with the planner's brief
3. **Visual Render** — Playwright screenshots analyzed by Claude Vision for visual quality

The pipeline passes when the weighted overall score reaches **7.5/10** with no critical issues.

## TECHNICAL HIGHLIGHTS

- **LangGraph orchestration** — State machine with conditional edges for approval/replan loops
- **3-agent architecture** — Each agent uses the LLM best suited for its task (strategy, coding, review)
- **Parallel validation** — Three independent checks run concurrently via `asyncio.gather`
- **Vision-based QA** — Screenshots are sent to Claude Vision for visual evaluation
- **Thread + Queue bridge** — Async pipeline runs in a background thread, streaming status messages to the Gradio UI in real-time
- **Structured output** — Pydantic models enforce consistent agent responses (ParsedGuidelines, ValidationReport)
- **User feedback loop** — After initial generation, users can iterate with natural language improvements

## HOW TO USE IT

### Prerequisites

- Python 3.12+
- API keys for OpenAI, Google (Gemini), and Anthropic

### Setup

```bash
cd 4_langgraph/community_contributions/blt909

# Create virtual environment
uv venv
source .venv/bin/activate

# Install dependencies
uv pip install -r requirements.txt

# Install Playwright browsers (once)
playwright install chromium

# Set API keys in .env
cat > .env << EOF
OPENAI_API_KEY=sk-...
GOOGLE_API_KEY=...
ANTHROPIC_API_KEY=sk-ant-...
EOF
```

### Run

```bash
# From the repository root
uv run 4_langgraph/community_contributions/blt909/app.py

# Or from the project directory
uv run app.py
```

Open `http://localhost:7862` in your browser.

### Usage

1. **Describe your homepage** — Type a natural language prompt (e.g., "Bold tech startup landing page for a fleet tracking SaaS, dark theme, trustworthy feel")
2. **Watch the pipeline** — Status updates stream in real-time as each agent works
3. **Review the output** — Check `output/homepage.html` and the generated screenshots
4. **Iterate** — Type improvement requests and click "Improve" to refine the result
5. **Start fresh** — Click "New project" to reset and begin again

### Output Files

| File | Description |
|------|-------------|
| `output/homepage.html` | Complete self-contained HTML page |
| `output/screenshot.png` | Desktop viewport screenshot (1280×900) |
| `output/screenshot_mobile.png` | Mobile viewport screenshot (375×812) |
