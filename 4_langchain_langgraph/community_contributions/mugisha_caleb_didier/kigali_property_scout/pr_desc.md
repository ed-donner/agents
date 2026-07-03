# Description

Added a community contribution for Week 4 Exercise.

Conversational LangGraph agent that helps users find real estate in Kigali, Rwanda. Gathers preferences (budget, type, purpose, area) through chat, searches via Serper API, and presents up to 4 structured opportunity cards in a two-column Gradio UI with SqliteSaver persistence.

**LangGraph concepts:** StateGraph, typed State, conditional routing, bind_tools + ToolNode, Pydantic structured output, SqliteSaver checkpointer, thread-based session isolation.

**Files:** `4_langgraph/community_contributions/mugisha_caleb_didier/kigali_property_scout/` — main.py, agent/ (state, tools, nodes, graph), ui/ (app)

**Checklist:**
- [x] Only community contributions modified
- [x] No API keys or .env files included
- [x] Under 1,000 lines (543 lines)
