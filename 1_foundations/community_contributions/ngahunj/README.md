# 🤖 AI Personal Website Assistant

This project is a conversational AI agent that represents **Ngahunj** on a personal website. It answers questions about experience, guides users toward opportunities, and captures leads (emails) using lightweight tools.

---

## 🚀 Features

* 💬 Chat interface (Gradio)
* 🧠 Resume-aware responses (PDF parsing)
* 🛠️ Tool system (lead capture + unknown questions)
* 🔁 Self-evaluation loop (improves responses automatically)
* ⚡ Powered by OpenRouter free models

---

## 🧱 Tech Stack

* Python
* OpenAI SDK (via OpenRouter)
* Gradio
* Pydantic
* PyPDF

---

## ⚙️ Setup

### 1. Clone the repo

```bash
git clone <repo-url>
cd project
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Add environment variables

Create a `.env` file:

```env
OPENROUTER_API_KEY=your_key_here
PUSHOVER_TOKEN=your_token
PUSHOVER_USER=your_user
```

---

## ▶️ Run the app

```bash
python app.py
```

Then open the local Gradio URL in your browser.

---

## 🧠 Models Used

* Chat: `z-ai/glm-4.5-air:free`
* Evaluation: `openai/gpt-oss-120b:free`

---

## 🛠️ Tools

The assistant can:

* Capture user emails for follow-up
* Log unanswered (relevant) questions

---

## 📁 Structure

```
app.py         # UI entry point
agent.py       # Core chat logic
evaluator.py   # Response quality control
tools.py       # Tool functions
prompts.py     # System prompts
config.py      # Settings
utils.py       # Helpers
```

---

## ⚠️ Notes

* Uses OpenRouter (not native OpenAI endpoint)
* Tool calling is simulated via prompt parsing
* Free models may be slower or rate-limited

---