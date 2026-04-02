# K8s Health MCP (Week 6)

This folder is a small **Model Context Protocol (MCP)** demo: fake Kubernetes health data is served by a Python MCP server, and an **OpenAI Agents** client talks to it over stdio. You do **not** need a real cluster to run it—that part is optional practice.

## Where to start

If you like a guided flow with screenshots and copy-paste commands, open **`week6_k8s_health_mcp.ipynb`** in Jupyter or VS Code. The notebook explains how the mock data differs from a live `kubectl` cluster, how to install, and what to do when something breaks.

If you only want to run the agent from a terminal, jump to **Quick start** below.

## What’s here

- **`week6_k8s_health_mcp.ipynb`** — Main walkthrough (recommended first read)
- **`sample_cluster.json`** — Mock cluster snapshot the tools read from
- **`server.py`** — MCP server (FastMCP tools + runbook resource)
- **`agent_client.py`** — Agent that launches `server.py` for you; don’t start the server by hand for normal use
- **`requirements.txt`** — Python dependencies
- **`agent_run_example.png`** / **`kind_kubectl_learning_ns.png`** — Example screenshots (MCP run vs mock data, and optional kind/`kubectl`)

## Quick start

1. `cd` into this directory.
2. Create a venv, then: `pip install -r requirements.txt`
3. Make sure **`OPENAI_API_KEY`** is set. Easiest match with the code: put a **`.env`** file at the **repository root** (the folder that contains `6_mcp/`), or export the variable in your shell.
4. Run:

```bash
python agent_client.py "Call cluster_overview, then namespace_health for payments."
```

**Note:** Do not run `python server.py` yourself for this flow—the client spawns it when it starts.
