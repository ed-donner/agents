# Timothy Supply Chain Optimization Platform

This is a modular, multi-agent supply chain optimization platform . It features:
- Real database access (SQLite)
- Error handling and logging
- Secure API key management
- Interactive Gradio dashboard
- Asynchronous agent-to-agent communication via MCP tools

## Features
- Inventory, Logistics, and Demand Forecasting agents
- LLM integration via OpenRouter
- Gradio dashboard for monitoring and interaction
- Dropdown and details for product-level insights
- MCP tool decorators for modular agent actions

## How to Run
1. Install requirements:
   ```sh
   pip install -r requirements.txt
   ```
2. Copy `.env.example` to `.env` and set your `OPENROUTER_API_KEY` and any other secrets.
3. To launch the interactive dashboard:
   ```sh
   python app.py
   ```
   This will open a browser window with the Gradio UI. You can:
   - View inventory, logistics, and demand forecast data
   - Select a product to see details and request a new forecast
   - See live agent-to-agent communication in action
4. (Optional) To run the orchestrator for automated agent workflows:
   ```sh
   python orchestrator.py
   ```
   This is for background/batch agent coordination and is not required for normal UI usage.

## Security & Deployment
- Store all secrets in `.env` (never commit real keys)
- Use HTTPS in production
- Set up proper logging and monitoring
- Deploy with a WSGI server (e.g., gunicorn, uvicorn) for scale

## Folder Structure
- `app.py` — Main Gradio UI and orchestration
- `orchestrator.py` — Async agent workflow runner (optional)
- `timothy_agents.py` — Agent classes and MCP tool registration
- `timothy_db.py` — Data access (SQLite)
- `timothy_llm.py` — LLM integration
- `timothy_mcp.py` — MCP bus and decorator
- `timothy_mcp_tools.py` — MCP tool wrappers

## Extending
- Add more agents (e.g., Procurement, Risk)
- Connect to real databases/APIs
- Enhance agent logic and LLM prompts
- Add authentication and user management
- Add more interactive UI elements (buttons, charts, etc.)

## FAQ
**Q: Do I need to run the orchestrator before the Gradio app?**
A: No. The Gradio app is fully self-contained. The orchestrator is only for background/batch workflows.

**Q: How do agents communicate?**
A: All agent-to-agent communication is handled asynchronously via the MCP bus and tool decorators.

**Q: How do I request a new forecast?**
A: Select a product in the Inventory tab and the UI will show a fresh forecast for that product.
