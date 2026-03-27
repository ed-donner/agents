# 🤖 Sidekick — Your Personal AI Co-worker

A LangGraph-powered AI assistant with a worker-evaluator loop, input/output guardrails, streaming responses, and session-isolated Gradio UI.

---

## What It Does

Sidekick takes a task, acts on it using tools, then self-evaluates whether it succeeded — retrying up to 3 times before returning a final response.

---

## Tools

| Tool | Description |
|---|---|
| 🔍 Web Search | Searches the web via DuckDuckGo |
| 📖 Wikipedia | Looks up factual information |
| 🔔 Pushover | Sends real push notifications to your phone |
| 📁 File System | Reads/writes files in a sandboxed `workspace/` folder |
| 🐍 Python REPL | Runs Python code with dangerous imports blocked |

---

## Architecture

```
User Message
     │
     ▼
input_guardrail()        ← blocks injections, policy violations
     │
     ▼
Worker Agent             ← uses tools to complete the task (temp=0.2)
     │
     ▼
Evaluator Agent          ← judges if task is done (temp=0.0)
     │
  ┌──┴──┐
PASS   RETRY (up to 3x)
  │
  ▼
output_guardrail()       ← sanitizes response, caps length
  │
  ▼
Streaming Gradio Response
```

---

## PR Checklist

- ✅ Model parameters — `temperature=0.2` (worker), `temperature=0.0` (evaluator), `max_tokens` capped
- ✅ Input & output guardrails — prompt injection checks, PII stubs, content sanitization
- ✅ Streaming — worker LLM streams tokens progressively to Gradio UI
- ✅ Exception handling — all tools and agent nodes wrapped in `try/except`
- ✅ Session isolation — each user gets their own `Sidekick` instance via `gr.State`

---

## Setup

```bash
git clone <repo>
cd silasamisi
python -m venv .venv
.venv\Scripts\activate       # Windows
pip install -r requirements.txt
playwright install
```

Create a `.env` file:
```
OPENAI_API_KEY=your-key
PUSHOVER_TOKEN=your-token
PUSHOVER_USER=your-user
```

Run:
```bash
python app.py
```

---

## Screenshots

<!-- Push notification demo -->

<!-- Wikipedia research demo -->

<!-- Terminal showing app running -->

---

## Demo Video

[▶ Watch Demo on Loom](https://www.loom.com/share/6a90b2e6504c4b90ae5a82c207ac8c70)

---

## File Structure

```
silasamisi/
├── app.py            # All-in-one: tools, guardrails, agent, UI
├── requirements.txt
├── .env              # Not committed
├── workspace/        # Sandboxed file system for agent
└── README.md
```
