# Mailjet Reply Webhook - Setup Guide

## Prerequisites

- Python virtual environment with dependencies installed
- Mailjet account with API keys configured
- ngrok installed (https://ngrok.com/download)

## Step 1: Start the Webhook Server

Open a terminal and run:

```bash
cd c:\Dev\Learning\ai_engineer_agentic_track\agents_mine\agents
.venv\Scripts\uvicorn.exe 2_openai.community_contributions.eliza_zadura.reply_webhook:app --port 8000
```

Verify it's running by visiting: http://127.0.0.1:8000/

You should see:
```json
{"status":"running","service":"Mailjet Reply Webhook"}
```

## Step 2: Expose via ngrok

Open another terminal and run:

```bash
ngrok http 8000
```

Copy the HTTPS forwarding URL (e.g., `https://abc123.ngrok-free.app`)

> **Note:** The ngrok URL changes each time you restart it (unless you have a paid plan with reserved domains).

## Step 3: Configure Mailjet Parse API

1. Log in to Mailjet: https://app.mailjet.com/

2. Navigate to **Transactional** → **Inbound** → **Parse Routes**

3. Click **Create a Parse Route**:
   - **Email address:** Create or choose a parseable address (e.g., `reply@parse.yourdomain.com`)
   - **Webhook URL:** Paste your ngrok URL + `/webhook/reply`
     - Example: `https://abc123.ngrok-free.app/webhook/reply`

4. Save the Parse Route

## Step 4: Configure Domain MX Records

For Mailjet to receive emails on your domain, you need to set up MX records:

1. In Mailjet, go to **Account Settings** → **Sender Domains & Addresses**

2. Add your domain and follow Mailjet's DNS configuration instructions

3. Add the MX record to your domain's DNS:
   - **Type:** MX
   - **Host:** `parse` (or your chosen subdomain)
   - **Value:** `parse.mailjet.com`
   - **Priority:** 10

4. Wait for DNS propagation (can take up to 48 hours, usually faster)

## Step 5: Test the Integration

1. Send an email TO the parse address you configured (e.g., `reply@parse.yourdomain.com`)

2. Mailjet will POST the email data to your webhook

3. The AI agent will craft a response and send it back via Mailjet

4. Check your inbox for the AI-generated reply!

## Troubleshooting

### Webhook not receiving requests
- Ensure ngrok is running and the URL is correct in Mailjet
- Check the ngrok web interface at http://127.0.0.1:4040 to see incoming requests

### Emails not sending
- Verify your Mailjet API keys are correct in `.env`
- Check that the sender email is verified in Mailjet

### Server errors
- Check the terminal running uvicorn for error messages
- Ensure all dependencies are installed: `pip install fastapi uvicorn mailjet-rest openai-agents`

## Architecture

```
Prospect replies to email
        ↓
    Mailjet receives email
        ↓
    Mailjet Parse API POSTs to ngrok
        ↓
    ngrok forwards to localhost:8000
        ↓
    FastAPI /webhook/reply endpoint
        ↓
    SDR Reply Agent (GPT-4o-mini)
        ↓
    send_reply tool → Mailjet API
        ↓
    Prospect receives AI response
```
