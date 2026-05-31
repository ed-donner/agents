### Step 1: Install dependencies (if not already)

From your project root / venv:

```bash
uv pip install sendgrid python-dotenv openai-agents gradio
```

(You likely already have `agents` and OpenAI SDK from the course setup.)

### Step 2: Set environment variables

In your `.env` (same place as other labs):

```env
OPENAI_API_KEY=sk-...your_openai_key...

# For email sending
SENDGRID_API_KEY=your_sendgrid_api_key_here
SENDGRID_SENDER_EMAIL=your_verified_sender@example.com
```

Make sure `SENDGRID_SENDER_EMAIL` is a **verified sender** in your SendGrid account
(just like in Week 2 Day 2/4 labs).

### Step 3: Run via CLI

```bash
python recipe_manager.py --cuisine "Idli Sambar" --email "test@gmail.com"
```

### Step 4: Run via Gradio UI

```bash
python gradio_app.py
```

What you’ll see:

* Trace ID + URL to inspect in **OpenAI traces**.
* Logs about:

  * Starting research
  * Running web search
  * Synthesizing recipe
  * Sending email
* The final recipe printed in Markdown in your terminal.
* An email in your inbox with a nicely formatted HTML recipe