---
name: Mailjet Reply Webhook
overview: Create a FastAPI webhook server that receives inbound email replies via Mailjet's Parse API and uses an AI agent to generate and send contextual responses.
todos:
  - id: create-webhook
    content: Create reply_webhook.py with FastAPI app, Mailjet send_reply tool, and SDR Reply Agent
    status: completed
  - id: test-local
    content: Test locally by running uvicorn and sending a manual POST request
    status: completed
  - id: setup-ngrok
    content: Run ngrok and note the public URL
    status: completed
  - id: configure-mailjet
    content: Set up Mailjet Parse Route pointing to ngrok URL (manual step with instructions)
    status: completed
---

# Mailjet Reply Webhook Implementation

## Why a Separate Python File (Not Notebook)

A webhook server needs to:
- Run continuously waiting for incoming HTTP requests
- Be exposable via ngrok to the internet
- Be started with `uvicorn` or similar ASGI server

Notebooks are designed for interactive, cell-by-cell execution — not for long-running servers. A `.py` file is the right choice here.

## Architecture

```mermaid
sequenceDiagram
    participant Prospect
    participant Mailjet
    participant ngrok
    participant FastAPI
    participant Agent
    
    Prospect->>Mailjet: Replies to sales email
    Mailjet->>ngrok: POST parsed email data
    ngrok->>FastAPI: Forward to /webhook/reply
    FastAPI->>Agent: Process reply with context
    Agent->>Mailjet: Send response via API
    Mailjet->>Prospect: Delivers AI response
```

## Implementation

### 1. Create `reply_webhook.py`

A new file in `2_openai/` containing:

- **FastAPI app** with a single POST endpoint `/webhook/reply`
- **`send_reply` tool** using Mailjet (matching your existing pattern)
- **SDR Reply Agent** that reads the inbound message and crafts a response
- Endpoint parses Mailjet's Parse API payload and triggers the agent

### 2. Mailjet Parse API Setup (Manual Steps)

You'll need to:
1. Set up a subdomain for receiving emails (e.g., `parse.yourdomain.com`)
2. Configure MX records to point to Mailjet
3. Create a Parse Route in Mailjet pointing to your ngrok URL

### 3. Running the Server

```bash
# Terminal 1: Start the webhook server
uvicorn reply_webhook:app --port 8000

# Terminal 2: Expose via ngrok
ngrok http 8000
```

Then configure Mailjet Parse Route to use the ngrok HTTPS URL.

## Key Differences from the Notebook Code

| Aspect | Notebook | Webhook Server |
|--------|----------|----------------|
| Execution | Cell-by-cell | Continuous server |
| Email direction | Outbound only | Inbound + Outbound |
| Trigger | You run a cell | HTTP POST from Mailjet |

## Files to Create

- `2_openai/reply_webhook.py` — the webhook server (~60 lines)