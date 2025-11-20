# Smart RAG Chatbot

A conversational AI that answers questions from your documents first, then falls back to general knowledge when needed. Plus, it keeps you in the loop with smart notifications.

## What it does

Think of it as your personal AI assistant that:
- **Knows your stuff** - Searches your documents first to answer questions
- **Stays helpful** - Uses general AI knowledge when your docs don't have the answer  
- **Keeps you informed** - Sends notifications when it goes beyond your knowledge base
- **Remembers conversations** - Maintains chat history and user details

## How it works

1. User asks a question
2. System searches your documents in `knowledge_base/`
3. **Found answer?** → Uses your docs and responds
4. **No answer?** → Uses general AI knowledge + sends you a notification
5. **Small talk?** → Quick friendly response

## Architecture

```
User Question → Search Your Docs → ChatGPT Response → Gemini Quality Check
                     ↓                                        ↓
              If no relevant docs                    If using general knowledge
                     ↓                                        ↓
              General AI Knowledge ← ← ← ← ← ← ← ← Pushover Notification
```

**Components:**
- **ChromaDB + LangChain**: Stores and searches your documents
- **ChatGPT**: Generates responses
- **Gemini**: Checks response quality  
- **Pushover**: Sends notifications
- **Gradio**: Simple web interface

## Quick Setup

1. **Install dependencies:**
```bash
pip install -r requirements.txt
```

2. **Create `.env` file with your API keys:**
```bash
OPENAI_API_KEY=your_openai_key
GOOGLE_API_KEY=your_gemini_key
PUSHOVER_USER=your_pushover_user  # optional
PUSHOVER_TOKEN=your_pushover_token  # optional
```

3. **Add your documents:**
Drop your `.txt`, `.md`, or `.markdown` files into the `knowledge_base/` folder

4. **Launch:**
```bash
python app.py
```

That's it! The web interface opens automatically.

## Key Features

- **Smart fallback**: Uses your docs first, general knowledge second
- **Quality control**: Built-in evaluator ensures good responses
- **Conversation memory**: Remembers chat history and user details
- **Smart notifications**: Only alerts when using general knowledge
- **Simple setup**: Just API keys and documents

## File Structure

```
├── app.py              # Web interface
├── controller.py       # Main logic
├── rag.py             # Document search
├── evaluator.py       # Quality checking
├── tools.py           # Notifications
├── knowledge_base/    # Your documents
└── .env               # API keys
```

## Example Usage

**Question about your docs:**
```
User: "What's our return policy?"
Bot: [Searches your docs] → [Finds policy] → [Answers from your content]
```

**General question:**
```
User: "What is machine learning?"
Bot: [No docs found] → [Uses AI knowledge] → [Sends notification] → [Helpful explanation]
```

Built with ChromaDB, LangChain, OpenAI, Gemini, and Gradio.