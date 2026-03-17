# Personal Chatbot - AI Assistant with Push Notifications

A personalized AI chatbot that answers questions about your career and sends push notifications to your phone when it needs your help or when someone wants to connect with you.

## 🚀 Features

- **Personalized Responses**: Chatbot answers questions based on your LinkedIn profile (`linkedin.pdf`) and personal summary (`summary.txt`)
- **Smart Escalation**: When the chatbot doesn't know an answer, you get a push notification on your phone
- **Connect Requests**: Users can request to stay in touch with you, triggering a notification
- **Mobile Notifications**: Uses Pushover to send instant notifications to your mobile device
- **Powered by OpenRouter**: Access to multiple LLM models through OpenRouter API
- **Gradio Interface**: Clean, user-friendly chat interface

## 📋 Prerequisites

Before you begin, make sure you have:
- Python 3.9+ installed
- A [Pushover](https://pushover.net/) account (for mobile notifications)
- An [OpenRouter](https://openrouter.ai/) API key
- Your LinkedIn profile as PDF
- A text file with your personal summary

## 🛠️ Installation

### 1. Clone the Repository
Move to the directory that contains the app.py file

### 2. Set Up Your Personal Files

Create a `me` folder in the project root and add your files:

```
me/
├── linkedin.pdf      # Your LinkedIn profile as PDF
└── summary.txt       # Your personal summary/bio
```

**Example `summary.txt`:**
```
I'm a Senior AI Engineer with 8 years of experience...
```

### 3. Install Dependencies

Using `uv` (recommended):
```bash
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uv pip install -r requirements.txt
```

Or using pip:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Create a `.env` file in the project root:

```env
# Required for notifications
PUSHOVER_TOKEN=your_pushover_app_token
PUSHOVER_USER_KEY=your_pushover_user_key

# Required for AI responses
OPENROUTER_API_KEY=your_openrouter_api_key
```

**Where to get these keys:**
- **Pushover**: Sign up at [pushover.net](https://pushover.net) → Get your User Key and create an Application Token
- **OpenRouter**: Sign up at [openrouter.ai](https://openrouter.ai) → Generate an API key

## 🎮 Running Locally

Start the chatbot:
```bash
uv run app.py
```

Or if using regular pip:
```bash
python app.py
```

The app will launch at `http://localhost:7860`

## ☁️ Deploy to Hugging Face Spaces

You can deploy this app to hugging face spaces.
