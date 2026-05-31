# Alter-Ego Chatbot

A professional chatbot that represents you on your website. It answers questions about your background, experience, and skills using Azure OpenAI and Gradio.

## What It Does

- Loads your professional info from a PDF resume/LinkedIn profile and text summary
- Responds to visitor questions about you using Azure OpenAI's GPT-4o-mini
- Captures interested visitor emails and logs unanswered questions
- Sends notifications via Pushover when users engage

## Quick Start

### Requirements
- Python 3.12+
- Azure OpenAI API key and deployment name
- Pushover API credentials (for notifications)

### Setup

1. **Clone and install dependencies:**
```bash
pip install -e .
```

2. **Create a `.env` file with:**
```bash
cp .env.example .env
```
Then edit `.env` with your actual values:
```
AZURE_OPENAI_API_KEY=your_key
AZURE_OPENAI_ENDPOINT=your_endpoint
AZURE_OPENAI_DEPLOYMENT=gpt-4o-mini
PUSHOVER_USER=your_pushover_user
PUSHOVER_TOKEN=your_pushover_token
```

3. **Add your data:**
   - Place your resume/LinkedIn PDF as `static/profile.pdf`
   - Create `static/summary.txt` with a brief professional summary

### Run It

```bash
python main.py
```

Opens a chat interface at `http://localhost:7860`

## How It Works

- **agent.py**: Main chat loop using Azure OpenAI
- **prompt.py**: Loads your profile data and builds the system prompt
- **tools.py**: Handles user email capture and logging unknown questions
- **main.py**: Launches the Gradio interface

## Customization

Edit `main.py` to change:
- Your name in `ConversationAgent(name="Your Name")`
- Chat title and description
- Example questions

## Notes

- Make sure `static/profile.pdf` and `static/summary.txt` exist or the agent will use placeholder text
- The chatbot stays in character as you and prioritizes answering from your provided context
