# RAG Chat Evaluator Bot

A lightweight chatbot app that uses LangChain RAG for chunk retrieval, OpenAI for generation, and Gemini for response evaluation.

## 🔧 Features

- 📚 Retrieval-Augmented Generation (RAG) with LangChain + ChromaDB
- 🤖 Chat interface powered by OpenAI's GPT
- ✅ Gemini-based evaluator checks tone + accuracy
- 🛠️ Records user emails to Google Sheets or CSV fallback


## 🚀 Setup

1. Clone the repo:

```bash
git clone https://github.com/your-username/rag-chat-evaluator-bot.git
cd career-chats
```

2. Create a virtual environment:

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:

```bash
 install -r requirements.txt
```

2. Keys in `.env` file:
```
   GOOGLE_API_KEY=<your-api-key>
   OPENAI_API_KEY=<your-api-key>
   GOOGLE_CREDENTIALS_JSON=<b64encoded-json>
```


