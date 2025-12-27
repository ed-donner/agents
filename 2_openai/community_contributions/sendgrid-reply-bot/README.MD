# SendGrid Reply Bot (Agentic SDR Loop)

This project extends the Week 2 Agentic Framework lab by adding **inbound email reply handling** using SendGrid Inbound Parse and an autonomous Agent.

## What this adds

- Sends a cold outbound sales email using multiple drafting agents
- Receives user replies via SendGrid webhook
- Uses an Agent to reason over the inbound message
- Sends a contextual reply automatically
- Maintains conversation continuity via email (no chat UI)

## Architecture

SendGrid (Inbound Parse)
→ FastAPI webhook
→ Agent (OpenAI Agents SDK)
→ SendGrid outbound email

## Setup

1. Install dependencies
```bash
pip install -r requirements.txt

2. Configure environment variables

Create a .env file from the example template:
cp .env.example .env

Then update it with your SendGrid credentials:

SENDGRID_API_KEY=your_sendgrid_api_key
FROM_EMAIL=your_verified_sender@example.com

3. Run the webhook server

Start the FastAPI server locally:

python -m uvicorn reply_webhook:app --port 8000
The server will be available at:

http://127.0.0.1:8000

4. Expose the webhook using ngrok

Since SendGrid cannot reach localhost, expose the server publicly:

ngrok http 8000

Copy the generated HTTPS URL and configure SendGrid Inbound Parse to point to:

https://<ngrok-url>/webhooks/sendgrid/reply


```markdown
> Note: ngrok must be running while testing inbound replies.
> If the tunnel URL changes, update the SendGrid Inbound Parse configuration.

