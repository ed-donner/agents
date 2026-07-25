import gradio as gr
from agent import get_diagnostics

DESCRIPTION = """#Dev Environment Doctor

Your local dev environment diagnostic assistant. Here's what I can do:

- **Check environment variables** — validate a custom list of env vars, or scan the default set of common ones (`DATABASE_URL`, `ANTHROPIC_API_KEY`, `NODE_ENV`, etc.)
- **Check port availability** — tell you if a custom list of ports or the default set of commonly used dev ports (PostgreSQL, Redis, React, etc.) are free or currently in use
- **Check runtime versions** — detect installed versions of common runtimes like Python, Node, Go, Java, Rust, Docker, and more
- **Generate a full report** — run all of the above at once and get a single combined diagnostic summary

> **v1.0** — This is the initial release. More checks and features are on the way."""

with gr.Blocks() as app:
    gr.Markdown(DESCRIPTION)

    gr.ChatInterface(get_diagnostics, type="messages")

app.launch()