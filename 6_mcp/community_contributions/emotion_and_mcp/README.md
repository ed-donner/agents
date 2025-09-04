# Go MCP Server + Python Emotion API (Demo, CPU-Friendly)

This project demonstrates a clean, practical Model Context Protocol (MCP) server written in Go that calls a lightweight Python Emotion API (Hugging Face). It is designed to show how to expose a single, high-signal MCP tool (`emotion_detection`) to clients like Claude Desktop. The MCP server has been written to be easily extensible to add your own tools.

This is not a fine-tuned-model showcase. Instead, it intentionally uses a compact, off‑the‑shelf model to keep the focus on the integration pattern (Go MCP server ⇄ Python API) and a shareable, CPU‑first developer experience.

## Why this project?

- Clear demo of MCP integration: a focused tool calling a simple HTTP API
- CPU‑friendly: small Hugging Face model (~20MB), low latency, no GPU required
- Minimal surface area: one POST endpoint in Python, one MCP tool in Go
- Easy to run, easy to extend, easy to share with teams

## What’s inside

- `src/python_server/`: Flask API powered by the Hugging Face model `boltuix/bert-emotion` (13 emotions with emoji mapping)
- `src/mcp-go-server/`: Go MCP server that invokes the Python API and formats the result for MCP clients

Model reference: `boltuix/bert-emotion` — see model card for details and examples: `https://huggingface.co/boltuix/bert-emotion`

## Quick demo

Input: “I’m so excited about this new release!”
Output: `Emotion: Happiness 😄 (Confidence: ~98%)`

## Setup (assumes Python is installed)

You’ll run two processes:
1) Python Emotion API (Hugging Face model)
2) Go MCP Server (exposes `emotion_detection` to MCP clients)

### 1) Start the Emotion API (Python)
```
cd src/python_server
python3 -m venv ../venv
source ../venv/bin/activate
pip install --upgrade pip
# Install dependencies
pip install -r requirements.txt
# (Linux CPU-only alternative for PyTorch)
# pip install torch --index-url https://download.pytorch.org/whl/cpu
# pip install -r requirements.txt

python3 emotion_server.py
# API at: http://127.0.0.1:5001
# POST /predict {"text": "I am so happy today!"}
```

Notes:
- Python 3.9–3.13 recommended
- Runs on macOS and Linux without a GPU (pipeline defaults to CPU)

### 2) Build and run the MCP Server (Go) - for Go installation see: https://go.dev/doc/install
```
cd src/mcp-go-server
export PATH=$PATH:/usr/local/go/bin   # if needed
go version                            # Go 1.21+ recommended

# Build
go build -o ./bin/emotion-mcp-server ./main

# (Optional) run via supergateway HTTP bridge – see below
```

### MCP Server Deploymnet: Run via supergateway (HTTP bridge for stdio MCP) - to install Node see: https://nodejs.org/en/download/
Prerequisite: Node.js + npm (or corepack). Then:
```
# Install once (or use npx each time)
npm install -g supergateway

cd src/new_mcp_server/mcp-go-server
npx -y supergateway \
  --stdio "./bin/emotion-mcp-server" \
  --port 8000 \
  --baseUrl http://localhost:8000
```
This exposes the stdio MCP server at `http://localhost:8000` for simple HTTP testing tools.

Note: this can be run wihin Docker or Kubernetes. 

#### Installing Node.js and npm
- Linux (Debian/Ubuntu):
  - sudo apt update && sudo apt install -y curl
  - curl -fsSL https://deb.nodesource.com/setup_lts.x | sudo -E bash -
  - sudo apt install -y nodejs
- macOS:
  - Using Homebrew: `brew install node`
  - Or download installer from the Node.js downloads page (below)
- Windows:
  - Download and run the Windows installer from the Node.js downloads page

Recommended (cross‑platform) via nvm (Node Version Manager):
```
curl -fsSL https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.7/install.sh | bash
# restart your shell
nvm install --lts && nvm use --lts
```

References:
- Node.js downloads: https://nodejs.org/en/download
- nvm (Node Version Manager): https://github.com/nvm-sh/nvm

## 3) Recommended: verify Emotion Server and MCP Server are working 
Assuming in a new termional:
```
cd src/tests
source ../venv/bin/activate 
python test_emotion_server.py
python test_mcp_server.py
```

# 4) UI: Use the gradio UI to exercise the services
Assuming venv active
```
cd src
python ui.py
```

### 5) Optional: Use with Claude Desktop
Add to your Claude Desktop config (path varies by OS):
```
{
  "mcpServers": {
    "emotion-detection": {
      "command": "/absolute/path/to/repo/src/new_mcp_server/mcp-go-server/bin/emotion-mcp-server",
      "env": {
        "EMOTION_SERVICE_URL": "http://localhost:5001/predict"
      }
    }
  }
}
```
Restart Claude Desktop and request emotion analysis on any text.

## Project layout
```
repo-root/
├── README.md                                  # This file (project overview)
└── src/
    └──-
        ├── python_server/                     # Flask + Hugging Face API
        │   ├── emotion_server.py
        │   ├── requirements.txt
        │   ├── start_server.sh
        │   └── (docs + tests)
        ├── mcp-go-server/                     # Go MCP server
        │   ├── main/
        │   │   ├── main.go
        │   │   └── tools.go
        │   └── bin/
        └── docs/
            └── mcp-go-server/
                ├── INSTRUCTIONS.md
                └── QUICK_START.md
```

## Support
- If the Python API won’t start, ensure dependencies are installed and port 5001 is free.
- If the MCP tool cannot reach the API, set `EMOTION_SERVICE_URL` to the correct base URL.
- On Linux without GPU, prefer the CPU‑only PyTorch wheel for smaller installs.
- For HTTP testing, install Node.js/npm to use supergateway (see above).
