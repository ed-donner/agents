# Emotion Detection MCP Server

This repo contains two components:

- `python_server/`: a lightweight Flask API using the BERT-Emotion model
- `mcp-go-server/`: an MCP server that exposes an `emotion_detection` tool

## Quick start

1) Start the Python emotion server
```
cd python_server
source ../venv/bin/activate || true
pip install -r requirements.txt
python3 emotion_server.py
```

2) Build and test the MCP server
```
cd ../mcp-go-server
export PATH=$PATH:/usr/local/go/bin
go build -o ./bin/emotion-mcp-server ./main
```

Now run the MCP smoke tests (recommended):
```
cd ../tests
./test_mcp.sh
```

## Docs & Tests

- Python server docs: `python_server/README.md`, `python_server/SETUP_GUIDE.md`
- MCP server docs: `docs/mcp-go-server/INSTRUCTIONS.md`, `docs/mcp-go-server/QUICK_START.md`
- Tests: `tests/test_emotion_server.py`, `tests/test_mcp.sh`

## Configuration

- Emotion API: `http://localhost:5001/predict`
- MCP env var: `EMOTION_SERVICE_URL=http://localhost:5001/predict`
