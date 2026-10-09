# Sidekick: Your Personal Co-Worker AI Agent

Sidekick is an agentic AI assistant built with **Langgraph**, **LangChain**, and **Gradio**. It can:

- **Google Calendar Integration**: Create and list events via the Calendar API.
- **Multi-Agent Orchestration**:
  - **PlannerAgent**: Decomposes tasks into subtasks.
  - **ResearchAgent**: Performs web searches & fetches summaries.
  - **CodeAgent**: Writes and debugs code.
- **Evaluator Loop**: Ensures responses meet success criteria or asks clarifying questions.
- **Push Notifications**: (Optional) Send reminders via Pushover.

---

## 🛠️ Prerequisites

- **Python 3.8+**
- **Google Cloud Project** with Calendar API enabled
- **OAuth 2.0 Client Credentials** (`credentials.json`)
- **Pushover** account & tokens (optional)
- **Virtualenv** or Conda environment

---

## 🚀 Installation

1. **Clone the repository**

   ```bash
   git clone https://github.com/yourusername/sidekick-agent.git
   cd sidekick-agent
   ```

2. **Create & activate a virtual environment**

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate      # macOS/Linux
   .venv\Scripts\activate       # Windows
   ```

3. **Install dependencies**

   ```bash
   pip install --upgrade pip
   pip install \
     python-dotenv \
     gradio \
     playwright \
     google-api-python-client \
     google-auth-httplib2 \
     google-auth-oauthlib \
     langchain \
     langchain-community \
     langchain-experimental \
     langchain-openai \
     langgraph \
     pydantic \
     requests
   playwright install chromium
   ```

---

## 🔑 Configuration

Create a `.env` file in the project root:

```ini
# OpenAI
OPENAI_API_KEY=sk-…

# Pushover (optional)
PUSHOVER_TOKEN=your_pushover_app_token
PUSHOVER_USER=your_pushover_user_key

# Google Calendar
GOOGLE_TOKEN_PATH=token.json
GOOGLE_CALENDAR_ID=primary

# File-Toolkit root (optional)
FILE_TOOL_ROOT=./sandbox

# Timezone for RFC3339 formatting
TIMEZONE_OFFSET=+05:30
```

---

## 🔑 OAuth2 Quickstart (Generate `token.json`)

1. **Enable the Calendar API** in Google Cloud Console.
2. Download your OAuth **client_secrets** file and save as `credentials.json` in the root.
3. Run this script once to authorize and generate `token.json`:
   ```python
   from google_auth_oauthlib.flow import InstalledAppFlow

   SCOPES = ["https://www.googleapis.com/auth/calendar"]
   flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
   creds = flow.run_local_server(port=0)
   with open("token.json", "w") as token:
       token.write(creds.to_json())
   ```
4. Confirm `token.json` is present alongside `credentials.json`.

---

## 🔧 Usage

Activate the environment and launch the Gradio app:

```bash
# Activate venv
source .venv/bin/activate      # macOS/Linux
.venv\Scripts\activate       # Windows

# Run the app
python app.py
```

- Open the displayed local URL in your browser.
- Chat with Sidekick!
- Expand the “📆 Calendar” accordion to create or list events.
- Provide success criteria to guide the assistant.
- Use “Reset” to start a new session.

---

## ❓ Troubleshooting

- **403 Insufficient Permission**: Delete `token.json` and re-run the OAuth quickstart to grant the full calendar scope.
- **ModuleNotFoundError**: Ensure you installed packages inside the activated venv with `python -m pip install ...`.
- **Playwright errors**: Run `playwright install chromium` again in your environment.

---

## 📁 Project Structure

```
.
├── app.py
├── sidekick.py
├── sidekick_tools.py
├── credentials.json        # OAuth client secrets
├── token.json              # OAuth tokens (auto-generated)
├── .env
├── sandbox/                # (optional) for file-toolkit writes
└── test_insert_event.py    # Quickstart test for Calendar write
```

---

## 📄 License

Released under the **MIT License**. Feel free to fork, tweak, and contribute!
