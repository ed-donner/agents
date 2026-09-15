# Decision Brief Team

A current-information multi-agent app built with the OpenAI Agents SDK. Ask a decision
question, optionally add your own context, and the app creates a sourced decision brief.

The workflow plans five focused searches and uses OpenAI's built-in `WebSearchTool` to gather
current evidence. Three reviewers then analyze the evidence in parallel:

- **Strategy Reviewer** checks goals, trade-offs, stakeholders, and alternatives.
- **Risk Reviewer** identifies failure modes, assumptions, and mitigations.
- **Execution Reviewer** focuses on feasibility, sequencing, and next steps.

A final agent combines their structured reviews into one recommendation, action plan, and a
list of the five or six strongest sources.

## Requirements

The repository root `.env` must contain:

```text
OPENAI_API_KEY=your-key
```

The optional `DEFAULT_MODEL_NAME` setting controls the model. If it is not set, the app
uses `gpt-5.4-mini`. You may also set `HOW_MANY_SEARCHES`; it defaults to `5`. No search
provider key or external service is required because web search is provided by OpenAI.

## Run

From the repository root:

```powershell
uv run python 2_openai/community_contributions/jualam_decision_brief/app.py
```

Open the local Gradio URL shown in the terminal, enter a decision question, and select
**Create decision brief**.

## How it works

The workflow uses structured Pydantic outputs, parallel searches, parallel specialist
reviews, and an OpenAI trace. Agents are instructed to prioritize recent authoritative
sources, preserve Markdown citations, label uncertainty, and never invent facts or links.
