# Google Calendar Agent

A natural language agent that creates Google Calendar events using [Claude](https://www.anthropic.com/claude) tool-use and the Google Calendar REST API.

The agent accepts plain English descriptions of appointments — including relative dates, durations, and locations — and handles all translation to structured API calls automatically.

---

## How It Works

```
User input (natural language)
        │
        ▼
  Claude (claude-sonnet-4)
  parses intent, extracts fields,
  calls create_calendar_event tool
        │
        ▼
  Google Calendar REST API
  POST /calendars/primary/events
        │
        ▼
  Event created — link returned
```

Claude is given a `create_calendar_event` tool with a defined JSON schema. It extracts the relevant fields from the user's request, calls the tool with structured arguments, and the agent executes the corresponding REST API call using the user's OAuth token. Claude then confirms what was created.

---

## Prerequisites

- Python 3.10+
- An [Anthropic API key](https://console.anthropic.com/)
- A Google account whose calendar you want to write to

---

## Installation

```bash
pip install anthropic python-dotenv google-auth google-auth-oauthlib requests
```

---

## Google Cloud Setup

You need OAuth 2.0 credentials to authorise access to Google Calendar. Follow these steps carefully — the credential **type** matters.

### 1. Create a Google Cloud Project

1. Go to [console.cloud.google.com](https://console.cloud.google.com/).
2. Click the project dropdown at the top → **New Project**.
3. Give it a name (e.g. `calendar-agent`) and click **Create**.
4. Make sure the new project is selected in the dropdown.

### 2. Enable the Google Calendar API

1. In the left sidebar, go to **APIs & Services → Library**.
2. Search for **Google Calendar API**.
3. Click on it, then click **Enable**.

### 3. Configure the OAuth Consent Screen

1. Go to **APIs & Services → OAuth consent screen**.
2. Select **External** and click **Create**.
3. Fill in the required fields:
   - **App name** — e.g. `Calendar Agent`
   - **User support email** — your email address
   - **Developer contact email** — your email address
4. Click **Save and Continue** through the Scopes and Test Users screens (you'll add a test user shortly).
5. On the final Summary screen, click **Back to Dashboard**.

### 4. Add Yourself as a Test User

While your app is in testing mode, only explicitly approved accounts can authorise it.

1. On the **OAuth consent screen** page, scroll to the **Test users** section.
2. Click **Add users** and enter your Google account email.
3. Click **Save**.

> **Note:** You can leave the app in testing mode indefinitely for personal use. The "app not verified" warning screen during OAuth can be bypassed by clicking **Advanced → Go to [App Name] (unsafe)**.

### 5. Create OAuth 2.0 Credentials

1. Go to **APIs & Services → Credentials**.
2. Click **Create Credentials → OAuth client ID**.
3. Set **Application type** to **Desktop app**.
4. Give it a name (e.g. `Calendar Agent Desktop`) and click **Create**.
5. A dialog will show your **Client ID** and **Client secret** — copy both.

> **Important:** The application type must be **Desktop app**, which produces an `installed` credential type. A **Web application** credential will not work with this agent.

---

## Environment Configuration

Create a `.env` file in the same directory as `calendar_agent.py`:

```env
CLAUDE_API_KEY=sk-ant-...
GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-client-secret
GOOGLE_PROJECT_ID=your-project-id
```

| Variable | Where to find it |
|---|---|
| `CLAUDE_API_KEY` | [Anthropic Console](https://console.anthropic.com/) → API Keys |
| `GOOGLE_CLIENT_ID` | Google Cloud Console → APIs & Services → Credentials |
| `GOOGLE_CLIENT_SECRET` | Google Cloud Console → APIs & Services → Credentials |
| `GOOGLE_PROJECT_ID` | Google Cloud Console → project dropdown (shown as the project ID, not name) |

---

## First Run — Browser Authorisation

On the first run, a browser window will open asking you to sign in and grant the agent permission to manage your calendar events. After you approve:

- A `token.json` file is written locally, containing your OAuth access and refresh tokens.
- Subsequent runs use this file automatically and refresh the token silently when it expires.
- Re-authentication is only needed if you delete `token.json` or revoke access in your Google account settings.

---

## Usage

**Single command:**

```bash
python3 calendar_agent.py "Dentist appointment on 25 June at 2pm for 1 hour"
```

**Interactive mode** (no argument):

```bash
python3 calendar_agent.py
```

```
📅 Calendar Agent — describe your appointment (or 'quit' to exit)

You: Team standup every Monday at 9am for 30 minutes
🔧 Calling: create_calendar_event
   {
     "summary": "Team standup",
     "start_datetime": "2026-06-08T09:00:00+01:00",
     "end_datetime": "2026-06-08T09:30:00+01:00"
   }
   ✅ Event created: https://www.google.com/calendar/event?eid=...
🤖 Done — "Team standup" has been added to your calendar on Monday 8 June at 9:00 AM.
```

The agent handles:

- Absolute dates: `"on 25 June"`, `"July 4th"`
- Relative dates: `"tomorrow"`, `"next Friday"`
- Durations: `"for 1 hour"`, `"for 45 minutes"`
- Locations: `"at the office"`, `"123 High Street"`
- Ambiguous requests: Claude will ask a single clarifying question if information is missing

---

## Security

**Never commit secrets to version control.** Add the following to your `.gitignore`:

```
.env
token.json
```

The `client_secret.json` file is not used by this agent — credentials are loaded from `.env` and the OAuth config is constructed in memory, so there is no secrets file to accidentally commit.

---

## Project Structure

```
calendar_agent.py   # Main agent script
.env                # Secret credentials (git-ignored)
token.json          # OAuth tokens written on first auth (git-ignored)
CALENDAR_AGENT.md   # This file
```

---

## Troubleshooting

**`EnvironmentError: GOOGLE_CLIENT_ID not found in .env`**
Your `.env` file is missing or in the wrong directory. It must be in the same directory as `calendar_agent.py`.

**"AgenticApps has not completed the Google verification process"**
You haven't added your Google account as a test user. Follow step 4 of the Google Cloud Setup above.

**`400 Bad Request` from the Calendar API**
Usually caused by a malformed datetime. Ensure your system clock is correct and that the request specifies a clear date and time.

**`token.json` causes auth errors after revoking access**
Delete `token.json` and re-run. A fresh browser auth flow will be triggered.

**Agent asks a clarifying question instead of creating the event**
The request is missing a required field — most commonly the time. Provide a more complete description, e.g. `"Lunch with Sarah on Friday at 1pm for 1 hour"`.