## Summary
- add the `ebunilo_langraph` Sidekick app with a Gradio UI, a LangGraph multi-agent workflow, and specialist tool routing for research, browser, and file tasks
- add SQLite-backed persistence for checkpoint memory and a per-username task library, plus automatic saving of successful runs
- improve the UX with conditional clarification gating, planner and specialist progress updates, and documentation for setup, usage, and troubleshooting

## Test plan
- [ ] Create a virtual environment and install dependencies from `requirements.txt`
- [ ] Run `playwright install chromium`
- [ ] Start the app with `python app.py`
- [ ] Verify a simple request runs immediately without clarifying questions
- [ ] Verify a complex or ambiguous request triggers 3 required clarifying questions before execution
- [ ] Verify planner and specialist progress messages appear in the chat
- [ ] Verify successful runs are saved to the task library for the selected username
- [ ] Verify returning with the same username restores the same SQLite-backed memory thread
