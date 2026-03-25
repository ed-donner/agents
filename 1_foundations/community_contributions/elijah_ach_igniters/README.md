# Personal Chatbot - AI Assistant with Push Notifications

A personalized AI chatbot that answers questions about your career and sends push notifications to your phone when it does not have answer to a question or when someone wants to connect with you.

## Features

- Answers questions based on your LinkedIn profile and personal summary
- Sends you a push notification when it doesn't know an answer
- Notifies you when a user wants to connect with you
- Built with Gradio, OpenRouter and OpenAI Agents SDK

## Prerequisites

- Python 3.9+
- A [Pushover](https://pushover.net) account
- An [OpenRouter](https://openrouter.ai) API key
- Your LinkedIn profile as a PDF and a short personal summary as a text file

## Getting Started

Clone the repo and move into the project directory. Then create a `me` folder and add your files:

```
me/
├── linkedin.pdf
└── summary.txt
```

Install dependencies:

```bash
uv venv
source .venv/bin/activate
uv pip install -r requirements.txt
```

Create a `.env` file with your keys:

```env
PUSHOVER_TOKEN=your_pushover_app_token
PUSHOVER_USER_KEY=your_pushover_user_key
OPENROUTER_API_KEY=your_openrouter_api_key
```

Then run the app:

```bash
uv run app.py
```

The app will be available at `http://localhost:7860`.

## Deploying

You can deploy this to Hugging Face Spaces.

---