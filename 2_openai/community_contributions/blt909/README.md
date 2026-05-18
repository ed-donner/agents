# 📰 Deep Research Newsletter Agent

A sophisticated multi-agent system built with the OpenAI Agents SDK that automates the process of researching complex topics and delivering a professional newsletter via email.

## 🎯 GOAL

The primary objective of this project is to provide a seamless "one-stop-shop" for deep research. By simply providing a topic, the system:
1.  **Evaluates query clarity**: Ensures the input is specific enough for high-quality results.
2.  **Plans research**: Breaks down the topic into targeted search queries.
3.  **Conducts web research**: Gathers and summarizes information from across the web.
4.  **Synthesizes content**: Writes a journalistic-style newsletter.
5.  **Delivers via Email**: Formats the content into HTML and sends it to the user.

## 📦 DEPENDENCIES

The project relies on the following key libraries:
- **`openai-agents`**: The core SDK for building and orchestrating the agentic workflow.
- **`gradio`**: Provides the stunning, interactive web interface.
- **`openai`**: Used for communication with standard LLMs (GPT-4o, GPT-4o-mini).
- **`brevo-python`**: For sending transactional emails via the Brevo API.
- **`python-dotenv`**: For secure environment variable management.
- **`pydantic`**: For structured data validation and agent output types.

## 🛠️ SETUP

Follow these steps to get the project running locally:

### 1. Environment Configuration
Create a `.env` file in the project root with your API keys:
```env
OPENAI_API_KEY=your_openai_key
BREVO_API_KEY=your_brevo_key
```

### 2. Configure Email Settings
Before running, you **must** update the sender and recipient email addresses in the `email_agent.py` file:
- Open `app_agents/email_agent.py`.
- Locate the `send_email` function.
- Replace `[EMAIL_ADDRESS]` in the `sender` and `to` fields with valid email addresses.

### 3. Installation
Install the required packages using `pip` or `uv`:
```bash
uv pip install -r requirements.txt
```

### 4. Running the App
Launch the Gradio UI:
```bash
uv run ui.py
```

## ✨ TECHNICAL HIGHLIGHTS

- **Multi-Agent Orchestration**: Uses a specialized `Research Manager` to coordinate handoffs between `Planner`, `Search`, `Writer`, and `Email` agents.
- **Input Guardrails**: Features a `query_clarity_guardrail` that proactively asks clarifying questions if a user's query is too vague, preventing wasted API calls and poor results.
- **Parallel Research**: Search tasks are executed concurrently using `asyncio`, significantly reducing the time required for deep research.
- **Structured Outputs**: Leverages Pydantic models to ensure agents return consistent, machine-readable data (e.g., `WebSearchPlan`, `ReportData`).
- **Streaming UI**: The Gradio interface provides real-time status updates and streams the agent's "thinking" process to the user.
