# Real Estate City Matchmaker (MCP Implementation)

Welcome to the **City Matchmaker**, a production-grade demonstration of the Model Context Protocol (MCP) using the official `agents` SDK and Streamlit.

This agent acts as a personalized real estate and lifestyle AI assistant. It helps you decide which city to move to by dynamically querying an MCP server to fetch live (simulated) data about apartment availability, cost of living, and the local cultural vibe.

## Architecture

This module follows a clean, decoupled architecture:
1. **`matchmaker_server.py`**: A robust `FastMCP` server exposing three distinct tools over the `stdio` transport layer. It comes fully equipped with type checking and error boundaries.
2. **`backend.py`**: The agent controller layer. It securely handles `dotenv` secrets, overrides OpenAI routing vectors to leverage OpenRouter, and orchestrates the async lifecycle connecting the MCP schema to the LLM Runner.
3. **`matchmaker_ui.py`**: A synchronized Streamlit GUI that wraps the background MCP agent process and provides a chat-based user experience.

## Getting Started

1. Ensure your OpenRouter or OpenAI keys are set in the `.env` file at the root of the repository.
   ```bash
   OPENROUTER_API_KEY=sk-or-v1-...
   ```
2. Make sure you have navigated to this directory.
   ```bash
   cd 6_mcp/community_contributions/must_mcp_week6
   ```
3. Run the Streamlit application.
   ```bash
   uv run streamlit run matchmaker_ui.py
   ```

Enjoy exploring the possibilities of MCP natively within Streamlit!
