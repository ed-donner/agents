# Local SideKick Agent

This project implements a secure and extensible **AI Agent** that runs entirely on your local system using [Ollama](https://ollama.com), with integrated **Docker-based Python REPL**, **DuckDuckGo web search**, and **Telegram notifications**.


## Features

- **Local LLM (Ollama)** — Uses any local model (e.g. `llama3.2`, `qwen2.5`) through the OpenAI-compatible API.
- **WebSearchTool** — Performs real-time DuckDuckGo searches.
- **Secure Python REPL** — Executes Python code safely inside an ephemeral Docker container with strict CPU, memory, and network isolation.
- **Telegram Notifications** — Sends updates or final results to a configured Telegram chat for asynchronous alerts.
- **Mostly offline** — No external API keys required; all processing can occur locally. Just use LangSmith to view logs online.



## Docker Image for Python REPL

The REPL tool runs untrusted Python code inside a minimal, non-privileged Docker container.

### Build the image

```bash
docker build -f Dockerfile.pyrepl -t pyrepl-sandbox:latest .
```

The REPL container runs with --network none, --read-only, and strict resource limits for safety.

### Security Notes

1. Each REPL call spins up a fresh container that is destroyed after execution.
2. No persistent volume mounts; no internet access inside containers.
3. Telegram is the only outbound integration (only when invoked).

