Perfect 😄 — here’s the **Markdown-optimized, GitHub-ready** version of your README.
It’s clean, scannable, and visually balanced while keeping all the key technical info.

---

# 🧠 Multimodal Agent News Summarizer

An AI-powered system that **aggregates news**, **summarizes using GPT-4o-mini**, and **creates audio briefings** with **MiniMax TTS**.
Built with the **official OpenAI Agents SDK** for real autonomous decision-making.

---

## 🚀 Features

* 🗞️ **Multi-Source Aggregation** – Fetches and merges RSS feeds from multiple topics
* 🧠 **AI Summarization** – GPT-4o-mini produces concise (≈300 words) audio-optimized briefs
* 🔊 **Text-to-Speech** – MiniMax TTS converts summaries to high-quality MP3
* 🤖 **Autonomous Agents** – Agents decide *when and how* to use tools
* ⚡ **Async/Await** – Fully asynchronous for speed and scalability
* 🎨 **Modern Gradio UI** – Simple blue-themed interface

---

## 🧩 Architecture

```
User → Orchestrator → Autonomous Agents
                ↓
   [1] News Aggregator → [2] Summarizer → [3] Audio Generator
```

Each agent independently chooses its tool:

| 🧩 Agent            | 🧰 Tool                    | 🎯 Purpose                |
| :------------------ | :------------------------- | :------------------------ |
| **Aggregator**      | `aggregate_news(topic)`    | Fetch & merge articles    |
| **Summarizer**      | `summarize_articles(json)` | Create engaging briefings |
| **Audio Generator** | `synthesize_speech(text)`  | Generate MP3 audio        |

---

<details>
<summary>⚙️ Installation & Setup</summary>

### Prerequisites

* Python 3.13 +
* pip

### 1️⃣ Install

```bash
git clone <repo>
cd news_summariser
python -m venv .venv && source .venv/bin/activate
pip install -e .
```

### 2️⃣ Environment Variables

Create a `.env` file in the root:

```env
OPENAI_API_KEY=your_openai_api_key
MINIMAX_API_KEY=your_minimax_api_key
```

</details>

---

<details>
<summary>▶️ Usage</summary>

```bash
python main.py
```

Then open the Gradio UI (default → [http://127.0.0.1:7860](http://127.0.0.1:7860)).

**Steps**

1. Pick a topic → Tech | World | Business | Politics | Sports
2. Click **Submit** to generate a summary + audio briefing

</details>

---

## 🏗️ Project Structure

```
news_summariser/
├── news_agents/
│   ├── news_aggregator.py
│   ├── summarizer.py
│   └── audio_generator.py
├── orchestrator.py
├── main.py
├── config/
└── README.md
```

---

## 🧠 Tech Stack

| Category             | Technologies           |
| :------------------- | :--------------------- |
| **LLM**              | OpenAI GPT-4o-mini     |
| **TTS**              | MiniMax API            |
| **Framework**        | OpenAI Agents SDK      |
| **Web UI**           | Gradio                 |
| **Async Runtime**    | aiohttp · aiofiles     |
| **Feeds**            | feedparser             |
| **Config & Logging** | python-dotenv · loguru |

---

## 📊 Example Output

```bash
✓ Fetched 15 articles
✓ Summary created (287 words)
✓ Audio generated: news_summary_20251109.mp3
```

📰 **Text Summary:** Engaging 300-word brief (opening hook → top 3 stories → closing)
🔊 **Audio File:** MP3 briefing ready for listening on the go

---

## 💡 Why This Matters

| Traditional Pipelines     | This Project (Autonomous Agents)         |
| :------------------------ | :--------------------------------------- |
| Hard-coded function calls | Agents decide tools autonomously         |
| Fixed sequence            | Dynamic reasoning + error recovery       |
| Rigid logic               | Extensible and maintainable architecture |

**Benefits**

* 🔁 Change behavior by editing instructions (not code)
* 🧩 Easily add new tools or agents
* 🧱 Fewer hard-coded flows → cleaner design

---

## 🔗 Resources

* 📘 [OpenAI Agents SDK Docs](https://openai.github.io/openai-agents-python/)
* 🎧 [MiniMax TTS API](https://www.minimaxi.com/)
* 🎨 [Gradio Docs](https://www.gradio.app/docs)

---

> **Built with the Official OpenAI Agents SDK 🚀**
> Keep your `.env` file secure — it’s already ignored by Git.

---

Would you like me to include a **short “How to extend this project”** section (e.g., adding new tools or agents) at the end? It makes the README feel even more “developer-friendly” for open-source contributors.
