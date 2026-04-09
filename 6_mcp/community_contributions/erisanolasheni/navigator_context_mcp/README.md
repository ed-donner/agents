## Navigator context MCP (Week 6 community contribution)

Small **stdio** MCP server that stores a **problem statement**, a **success metric**, and **timestamped session notes**, then exposes a **`get_briefing_for_prompt`** tool so an agent (or you) can pull that context into a prompt—aligned with the course themes: problem-first, measurable success, workflow logging, and “what goes in the prompt.”

### Run the server

From the repo root (with course dependencies installed):

```bash
cd 6_mcp/community_contributions/erisanolasheni/navigator_context_mcp
uv run navigator_server.py
```

State is persisted in `.navigator_state.json` next to the server (do not commit this file if you run locally).

### Try the demo notebook

Open `navigator_demo.ipynb` from this folder or from the repo root; it resolves the server path automatically when possible.

### Tools

| Tool | Purpose |
|------|--------|
| `set_problem_statement` | Capture the problem you are solving |
| `set_success_metric` | Capture how you will know you succeeded |
| `append_session_note` | Log experiments, trace observations, or prompt changes |
| `list_session_notes` | Read recent notes |
| `get_briefing_for_prompt` | One block of text for system/developer context |
| `clear_navigator_state` | Reset (requires `confirm=true`) |
