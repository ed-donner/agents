# 🤖 Sidekick - Personal Co-Worker

An AI agent that completes tasks step-by-step with intelligent evaluation feedback. It integrates multiple tools to search the web, run code, manage files, and more.

## **Quick Start**

### **1. Setup**
```bash
# Clone and navigate to project
cd projects

# Install dependencies
uv sync

# Copy environment file
cp .env.example .env

# Add your API keys to .env
```

### **2. Get API Keys**
- **Azure OpenAI**: [Azure Portal](https://portal.azure.com)
- **Google Serper**: [serper.dev](https://serper.dev)
- **Pushover**: [pushover.net](https://pushover.net) (optional)

### **3. Run**
```bash
uv run app.py
```

Then open `http://127.0.0.1:7860` in your browser.

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
projects/
├── app.py              # Gradio UI interface
├── sidekick.py         # LangGraph agent logic
├── sidekick_tools.py   # Tool integrations
├── .env.example        # Environment template
└── sandbox/            # File storage
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
