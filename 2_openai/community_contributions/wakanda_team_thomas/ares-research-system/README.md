# 🛡️ ARES: Autonomous Research & Extraction System

ARES is a high-precision, multi-agent deep research engine built on the OpenAI Agents SDK (2026). Unlike traditional RAG systems, ARES utilizes a hierarchical orchestration pattern to plan, execute, and synthesize deep-dive research into structured HTML reports.

## 🚀 Key Features

- **Hierarchical Orchestration**: Uses a Lead Architect (Manager) to coordinate Specialists as tools.
- **MCP Integration**: Natively connects to Model Context Protocol servers for live web search and secure email delivery.
- **Persistent Sessions**: Powered by SQLiteSession to handle long-running research tasks without state loss.
- **Structured HTML Delivery**: Automatically generates executive-ready HTML reports with a strict 200-word executive summary and cited deep data.
- **Safety Guardrails**: Built-in Tripwires for PII detection and tool-input validation.
- **Gradio UI**: Interactive web interface for submitting queries, monitoring progress, and viewing research reports — deployed on Hugging Face Spaces.

## 🏗️ Architecture

ARES follows the **Manager-Specialist** design pattern:

- **Lead Architect (Manager)**: Generates a `ResearchPlan` (Pydantic-enforced) and delegating tasks.
- **Web Specialist (Researcher)**: An autonomous MCP-agent that performs recursive searches and fact extraction.
- **Narrative Editor (Synthesizer)**: Compiles raw data into semantic HTML and enforces the 200-word summary constraint.
- **Courier (Delivery)**: Handles OAuth-protected email delivery via an MCP Email Server.

## 🛠️ Setup

This project uses **uv** for ultra-fast dependency management and performance.

### 1. Installation

```bash
# Clone the repository
git clone https://github.com/youruser/ares-research
cd ares-research

# Sync dependencies and create virtual environment
uv sync
```

### 2. Configuration

Create a `.env` file in the root directory:

```
OPENAI_API_KEY=sk-proj-xxxx
BRAVE_SEARCH_API_KEY=xxxx  # For the Search MCP
SENDGRID_API_KEY=xxxx      # For the Email MCP
```

## 🚦 Usage

### CLI Mode

```bash
uv run main.py --query "Analyze the 2026 solid-state battery breakthroughs and their impact on EV sector stocks."
```

### Gradio UI (Local)

Launch the interactive web interface locally:

```bash
uv run app.py
```

Then open [http://localhost:7860](http://localhost:7860) in your browser.

### Hugging Face Spaces (Production)

ARES is deployed as a Gradio app on [Hugging Face Spaces](https://huggingface.co/spaces).

To deploy your own instance:

1. Create a new Space on Hugging Face with the **Gradio** SDK.
2. Add your API keys as **Secrets** in the Space settings:
   - `OPENAI_API_KEY`
   - `BRAVE_SEARCH_API_KEY`
   - `SENDGRID_API_KEY`
3. Push the repository to the Space:

```bash
git remote add hf https://huggingface.co/spaces/YOUR_USERNAME/ares-research
git push hf main
```

### Advanced: Lifecycle Hooks

ARES implements `on_tool_call` hooks for Human-in-the-Loop approvals. If a research plan exceeds a specific token budget, the system will pause and wait for manual confirmation in the CLI.

## 📦 Project Structure

```
├── ares_agents/     # Agent instructions & handoff logic
├── ares_tools/      # MCP Server connections & Python functions
├── ares_schema/     # Pydantic models for Structured Outputs
├── ares_data/       # SQLite persistent session database
├── main.py          # CLI entry point and Runner configuration
└── app.py           # Gradio web UI
```

## 🔒 Safety & Governance

- **Input Guardrails**: All user queries are vetted against a safety classifier before reaching the Architect.
- **Tool Input Validation**: The `send_email` tool is protected by a guardrail that ensures recipients match the authorized `UserContext`.
- **Traceability**: Every run generates a full SDK trace stored in `ares-data/sessions.db` for post-run auditing.

## 📄 License

Apache-2.0
