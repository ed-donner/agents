# Deep Research Agent

A Gradio application that coordinates AI agents to plan web searches, gather source material, write a structured research report, and notify the user.

## Goals and use cases

The project demonstrates a multi-agent research workflow for questions that benefit from gathering and synthesizing public web sources. It can help with early-stage background research, literature discovery, and topic exploration. It is an aid for research, not a substitute for checking primary sources or expert advice.

The lead agent is instructed to handle scientific topics. The workflow produces a research plan, a detailed Markdown report, follow-up questions, and a notification through email or Pushover.

## Architecture

The Gradio UI in `app.py` passes a query to `ResearchManager`:

1. The research agent asks the planner agent to produce web-search queries.
2. The search agent calls `search_web`, which queries DuckDuckGo and fetches excerpts from a limited number of result pages.
3. The writer agent synthesizes the collected material into a structured report.
4. The email agent sends a report notification using SMTP or Pushover, depending on configuration.

```text
Gradio UI -> ResearchManager -> Research agent
                                 ├── Planner agent
                                 ├── Search agent -> DuckDuckGo / result pages
                                 ├── Writer agent
                                 └── Email agent -> SMTP or Pushover
```

Agent instructions and response schemas are in `deep_research_agent.py` and `response_model.py`. The configured model client is created in `ai_model.py`. `simple.py` is an alternate minimal UI; use `app.py` as the main entry point.

## Requirements

- Python 3.10 or newer
- An API key and base URL for an OpenAI-compatible chat-completions endpoint that serves the configured model
- SMTP credentials if email notifications are enabled, or Pushover credentials if they are disabled
- Internet access for DuckDuckGo search and fetching public result pages

The default model name is `claude-haiku-4-5-20251001`. Configure `ANTHROPIC_API_KEY` and `ANTHROPIC_BASE_URL` for the compatible endpoint used by `ai_model.py`, or set `DEFAULT_MODEL_NAME` to a model supported by your endpoint. Provider billing and usage limits apply.

## Setup

From this project directory:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install pydantic python-dotenv openai openai-agents gradio requests httpx beautifulsoup4
```

On Windows PowerShell, activate the virtual environment with:

```powershell
.venv\Scripts\Activate.ps1
```

Create a local `.env` file in this directory and add the settings you need from the sections below. Never commit `.env` or share its contents.

### Model configuration

Add the following to `.env` for the model endpoint:

```dotenv
ANTHROPIC_API_KEY=
ANTHROPIC_BASE_URL=
DEFAULT_MODEL_NAME=claude-haiku-4-5-20251001
HOW_MANY_SEARCHES=5
```

`ANTHROPIC_BASE_URL` must be an endpoint compatible with the OpenAI Python client's chat-completions interface used by this project. The variable names reflect the current implementation; they do not imply compatibility with every Anthropic endpoint.

### Notification configuration

Email is enabled by default. Set `EMAIL_ADDRESS`, `EMAIL_SMTP_SERVER`, and `EMAIL_APP_PASSWORD` to use SMTP. The app sends the generated report notification to the configured email address.

To use Pushover instead, set `USE_EMAIL=false` and provide `PUSHOVER_USER` and `PUSHOVER_TOKEN`. Configure the selected notification provider before running research; the workflow attempts to send a notification after writing the report.

## Run

Launch the Gradio interface:

```bash
python app.py
```

Open the local URL printed by Gradio, enter a research question, and select **Investigate**. Searches and model calls require network access and may incur provider charges. Research also sends a notification using the configured provider.

## Project files

```text
deep_research_anton/
├── app.py                 # Main Gradio interface
├── research_manager.py    # Orchestrates the streamed agent run
├── deep_research_agent.py # Lead agent and specialist-agent tools
├── planner_agent.py       # Search-plan agent
├── search_agent.py        # Web-search summarizer
├── search_tool.py         # DuckDuckGo search and page excerpts
├── writer_agent.py        # Report writer
├── email_agent.py         # Email/Pushover notification agent
├── messenger.py           # SMTP and Pushover integrations
├── response_model.py      # Pydantic output schemas
├── ai_model.py            # Model client configuration
├── styles.py              # Gradio layout, examples, and styling
├── simple.py              # Alternate minimal Gradio interface
```

## Limitations

- Search results and fetched page excerpts depend on third-party sites and may be incomplete, unavailable, or inaccurate.
- Review citations and claims against original sources before relying on the report.
- The workflow can send email or push notifications and makes external model and search requests; do not submit sensitive information.
- The current implementation does not provide automated fact verification or a formal citation audit.
