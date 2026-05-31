# CodeBuilder

A Python project that uses LangGraph, Ollama, and web search to generate code projects based on user challenges.

## Features

- LangGraph state management for workflow orchestration
- Ollama integration with llama3.2 for plan generation
- Custom DuckDuckGo web search for code examples
- FastAPI backend with REST and WebSocket support
- Gradio UI for interactive project creation
- Automatic project generation in sandbox directory

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Ensure Ollama is running with llama3.2 model:
```bash
ollama pull llama3.2
```

3. Start the FastAPI backend:
```bash
uvicorn backend.main:api --reload --port 8000
```

4. In another terminal, start the Gradio UI:
```bash
python -m frontend.gradio_ui
```

## Usage

1. Open the Gradio UI (typically at http://localhost:7860)
2. Enter your project challenge in the input box
3. Click "Submit Challenge"
4. Enter the programming language
5. Click "Submit Language"
6. Review the generated plan
7. Click "Build Project" to create files in the sandbox directory

## Project Structure

- `backend/` - Core application code
- `sandbox/` - Generated projects (gitignored)
