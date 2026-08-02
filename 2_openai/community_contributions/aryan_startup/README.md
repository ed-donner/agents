---
title: Startup Due Diligence
emoji: 📈
colorFrom: blue
colorTo: indigo
sdk: gradio
sdk_version: 6.15.2
app_file: app.py
pinned: false
---

# Startup Due Diligence Agent

A multi-agent demo workflow for conducting deep research and due diligence on startup ideas, compiling findings into a structured report, and emailing it to a recipient.

🔗 **Live Demo**: [Hugging Face Space](https://huggingface.co/spaces/notaryxn/startup_due_diligence)

---

## Architecture


1. **Planner Agent** ([planner_agent.py](file:///Users/notaryxn/Desktop/Startup%20Due%20Diligence%20Agent%20/planner_agent.py)): Takes the startup idea and drafts a target web search plan (up to 5 strategic queries).
2. **Search Agent** ([search_agent.py](file:///Users/notaryxn/Desktop/Startup%20Due%20Diligence%20Agent%20/search_agent.py)): Executes the web search queries using the built-in search tool and generates concise bullet-point findings.
3. **Writer Agent** ([writer_agent.py](file:///Users/notaryxn/Desktop/Startup%20Due%20Diligence%20Agent%20/writer_agent.py)): Synthesizes the search findings into a detailed Markdown report covering market size, competitors, risks, and investment recommendations.
4. **Email Agent** ([email_agent.py](file:///Users/notaryxn/Desktop/Startup%20Due%20Diligence%20Agent%20/email_agent.py)): Converts the Markdown report into HTML and sends it via **SendGrid** to the specified recipient.
5. **Research Manager** ([research_manager.py](file:///Users/notaryxn/Desktop/Startup%20Due%20Diligence%20Agent%20/research_manager.py)): Coordinates the asynchronous execution of the agents, passing state (search results, report, and recipient email) between them.

---

## How to Run Locally

### 1. Configure Environment Variables
Create a `.env` file in the root directory:
```env
GEMINI_API_KEY=your_gemini_api_key
SENDGRID_API_KEY=your_sendgrid_api_key
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Run the Gradio App
```bash
python app.py
```
This will launch the local Gradio interface in your default browser.
