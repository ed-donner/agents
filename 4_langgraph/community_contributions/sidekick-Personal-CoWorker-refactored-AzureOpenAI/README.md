# 🤖 Sidekick - Personal Co-Worker

An AI agent that completes tasks step-by-step with intelligent evaluation feedback. It integrates multiple tools to search the web, run code, manage files, and more.

## **Quick Start**

### **1. Install Dependencies**
```bash
# Using pip (recommended for all users)
pip install -e .

# Or using uv (faster alternative)
uv sync
```

### **2. Configure Environment**
```bash
# Copy the example environment file
cp .env.example .env

# Add your API keys to .env
```

**Required API Keys:**
- **Azure OpenAI**: Get from [Azure Portal](https://portal.azure.com)
- **Google Serper**: Get from [serper.dev](https://serper.dev)
- **Pushover** (optional): Get from [pushover.net](https://pushover.net)

### **3. Run the App**
```bash
# Using pip installation
python app.py

# Or using uv
uv run app.py
```

Open `http://127.0.0.1:7860` in your browser.

---

## **Features**

| Tool | What It Does |
|------|--------------|
| 🔍 **Web Search** | Find current information online |
| 🌐 **Browser** | Navigate websites and extract data |
| 📚 **Wikipedia** | Look up information from Wikipedia |
| 🐍 **Python REPL** | Execute Python code directly |
| 📁 **File Manager** | Create, read, write files |
| 📲 **Notifications** | Send push alerts |

---

## **How to Use**

1. **Enter your task** - e.g., "Find the current Bitcoin price"
2. **Set success criteria** - e.g., "Price in USD and EUR"
3. **Click Submit** - Agent works through the task
4. **Review output** - See results and evaluation

---

## **Tech Stack**

- **Framework**: LangGraph v0.2+ (Agent Orchestration)
- **UI**: Gradio 6.0 (Web Interface)
- **LLM**: Azure OpenAI
- **Browser**: Playwright
- **Async**: Python 3.10+ asyncio

---

## **Project Structure**

```
sidekick/
├── app.py              # Gradio UI
├── sidekick.py         # LangGraph agent
├── sidekick_tools.py   # Tool integrations
├── pyproject.toml      # Dependencies
├── .env.example        # Configuration template
└── README.md           # Documentation
```

---

## **Example Queries**

- "Search for latest AI news and summarize"
- "Write Python code to calculate Fibonacci numbers"
- "Create a file with sample data and parse it"
- "Visit Python.org and get the current version"

---

## **Requirements**

- Python 3.12
- Azure OpenAI API key
- Google Serper API key
- Pushover account for notifications

---