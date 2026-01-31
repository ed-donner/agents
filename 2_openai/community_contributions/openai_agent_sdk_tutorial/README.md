# OpenAI Agent SDK Tutorial

An educational project demonstrating key concepts of the OpenAI Agent SDK through working examples with comprehensive documentation.

## Features Demonstrated

This tutorial covers the following OpenAI Agent SDK concepts:

- **Agents**: Configuration with instructions, tools, guardrails, and hooks
- **Dynamic Instructions**: Generating context-aware system prompts at runtime
- **Function Tools**: Converting Python functions to LLM-callable tools with `@function_tool`
- **Tool Guardrails**: Input/output validation on tool calls (`@tool_input_guardrail`, `@tool_output_guardrail`)
- **Agent Guardrails**: Input/output validation on agent level (`@input_guardrail`, `@output_guardrail`)
- **Agents as Tools**: Using `agent.as_tool()` for agent composition
- **Handoffs**: Transferring control between agents
- **Lifecycle Hooks**: `RunHooks` and `AgentHooks` for observability
- **Session Memory**: Persisting conversation state with `SQLiteSession`
- **Tracing**: Using `trace()` for debugging and observability

## Installation

```bash
pip install openai-agents python-dotenv gradio
```

> **Note**: If you are running this app within the "agents" course virtual environment, these dependencies are already installed and no additional `pip install` is required.

## Environment Setup

Create a `.env` file with your API keys:

```env
OPENAI_API_KEY=your-openai-api-key

# Optional: For push notification tool
PUSHOVER_TOKEN=your-pushover-token
PUSHOVER_USER=your-pushover-user
```

## Usage

**Important**: Due to Python's package import system, run as a module from the parent directory:

```bash
cd 2_openai/community_contributions
python -m openai_agent_sdk_tutorial
```

### Command Line Options

```bash
python -m openai_agent_sdk_tutorial              # Normal mode
python -m openai_agent_sdk_tutorial --debug      # Enable debug logging
python -m openai_agent_sdk_tutorial -l app.log   # Write logs to file
```

## Project Structure

```
openai_agent_sdk_tutorial/
├── __init__.py      # Package initializer
├── __main__.py      # Entry point for `python -m` execution
├── app.py           # Gradio chat interface
├── agent.py         # Core agent configuration and execution
├── tool.py          # Function tools and tool guardrails
├── guardrail.py     # Agent-level input/output guardrails
├── handoff.py       # Agent-to-agent control transfer
├── hook.py          # Lifecycle callbacks (RunHooks, AgentHooks)
└── util.py          # Logging configuration utility
```

## Architecture

```
User Input (Gradio)
       │
       ▼
    app.py (main)
       │
       ▼
    agent.py (run_agent)
       ├── Input Guardrails (guardrail.py)
       ├── Dynamic Instructions
       ├── Agent Loop
       │   ├── LLM Calls (with hooks from hook.py)
       │   └── Tool Execution (tool.py)
       │       └── Tool Guardrails
       ├── Output Guardrails (guardrail.py)
       └── Handoff Support (handoff.py)
```

## Learning Path

1. **Start with `app.py`**: See how the Gradio interface connects to the agent
2. **Explore `agent.py`**: Understand agent configuration and the Runner
3. **Study `tool.py`**: Learn about function tools and tool guardrails
4. **Review `guardrail.py`**: See agent-level input/output validation
5. **Check `hook.py`**: Understand lifecycle callbacks
6. **Examine `handoff.py`**: Learn about agent-to-agent transfers

Each file contains extensive documentation explaining the concepts demonstrated.
