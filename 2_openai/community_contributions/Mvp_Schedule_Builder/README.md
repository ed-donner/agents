# MVP Schedule Builder 🚀

An intelligent product planning assistant that transforms your ideas into actionable development plans with integrated Google Calendar scheduling.

## 🎯 Overview 

This AI-powered tool helps entrepreneurs and developers plan and prioritize building an MVP from concept to completion. Using a multi-agent system, it provides comprehensive product analysis and creates realistic development schedules.

### Key Features

- **💡 Idea Critique**: Analyzes your product concept with detailed pros, cons, and improvement suggestions
- **📊 Market Research**: Investigates competitors and identifies market opportunities 
- **📋 Functional Requirements**: Generates prioritized feature lists based on market insights
- **📅 Smart Scheduling**: Creates realistic 4-week development timelines
- **🗓️ Google Calendar Integration**: Automatically syncs your project schedule to Google Calendar
- **🌐 Web Interface**: Beautiful Gradio-based UI for easy interaction

## 🛠️ Architecture

The system uses multiple specialized AI agents:

- **Market Researcher Agent**: Conducts competitor analysis and market validation
- **Idea Critiquer Agent**: Provides balanced feedback on product concepts  
- **Product Manager Agent**: Orchestrates requirements and scheduling
- **Scheduler Agent**: Creates detailed project timelines with dependencies
- **Calendar Integration Tool**: Syncs schedules to Google Calendar

## 🚀 Quick Start

### Prerequisites

```bash
# Install dependencies
uv add gradio openai python-dotenv google-api-python-client google-auth-httplib2 google-auth-oauthlib
```

### Environment Setup

1. Create a `.env` file with your API keys:
```bash
OPENAI_API_KEY=your_openai_api_key_here
```

2. Set up Google Calendar OAuth (for calendar integration):
   - Run the setup guide: `python setup_google_oauth.py`
   - Follow the detailed instructions to configure Google Cloud Console

### Running the Application

```bash
# Launch the web interface
uv run mvp_schedule_builder.py
```

The app will open in your browser at `http://localhost:7860`

## 🖥️ Usage

1. **Enter Your Idea**: Describe your product concept in the text box
2. **Get Comprehensive Analysis**: The system will:
   - Research the market and competitors
   - Critique your idea with pros/cons
   - Generate functional requirements  
   - Create a 4-week development schedule
3. **Calendar Integration**: Optionally sync the schedule to Google Calendar
4. **Review Results**: Get actionable insights and next steps

### Example Input
```
I want to build a mobile app that helps people find and book local fitness classes in their area, similar to ClassPass but focused on smaller, independent studios.
```

### Example Output
- Market analysis of fitness booking platforms
- Detailed critique with 3 pros and 3 cons
- Prioritized feature list (user auth, studio search, booking system, etc.)
- 4-week development timeline with specific tasks
- Google Calendar with scheduled development activities

## 📁 Project Structure

```
MVP_Schedule_Builder/
├── mvp_schedule_builder.py      # Main Gradio web application
├── product_planner.py           # Core orchestration logic
├── product_agents/              # AI agent implementations
│   ├── market_researcher_agent.py
│   ├── idea_critiquer_agent.py
│   ├── product_manager_agent.py
│   ├── scheduler_agent.py
│   └── base_model/              # Abstract base classes
├── tools/                       # Utility tools and integrations
│   └── calendar_integration.py  # Google Calendar API wrapper
├── setup_google_oauth.py        # OAuth setup guide
├── reset_auth.py               # Authentication reset utility
└── .env                        # Environment variables
```

## 🔧 Google Calendar Setup

### Method 1: OAuth 2.0 (Recommended)

1. **Create Google Cloud Project**:
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create new project or select existing one

2. **Enable Calendar API**:
   - Navigate to "APIs & Services > Library"
   - Search and enable "Google Calendar API"

3. **Configure OAuth Consent Screen**:
   - Go to "APIs & Services > OAuth consent screen"
   - Choose "External" user type
   - Fill required fields and add your email as test user

4. **Create OAuth Credentials**:
   - Go to "APIs & Services > Credentials"
   - Create "OAuth 2.0 Client ID" → "Desktop application"
   - Download JSON file as `credentials.json`

5. **Register Redirect URIs**:
   ```
   http://localhost:8080/
   http://localhost:8081/
   http://localhost:8082/
   ```

### Method 2: API Key (Limited Functionality)
Add `GOOGLE_CALENDAR_API_KEY` to your `.env` file (read-only access only).

## 🛠️ Development

### Running Individual Components

```bash
# Test market research agent
python -c "from product_agents import MarketResearcherAgent; agent = MarketResearcherAgent()"

# Test calendar integration  
python -c "from tools import GoogleCalendarIntegration; cal = GoogleCalendarIntegration()"

# Reset authentication if needed
python reset_auth.py --reset
```

### Customization

- **Modify timeline**: Change `num_weeks` parameter in `SchedulerAgent`
- **Add new agents**: Extend `AgentModel` base class
- **Custom tools**: Use `@function_tool` decorator
- **UI themes**: Modify Gradio theme in `mvp_schedule_builder.py`

## 🚨 Troubleshooting

### Common Issues

**"Access blocked: This app's request is invalid"**
- Register redirect URIs in Google Cloud Console
- Ensure OAuth consent screen is configured

**"CSRF Warning! State not equal in request and response"**  
- Close all Google auth browser tabs
- Clear browser cookies for Google accounts

**"Import errors"**
- Ensure all dependencies installed: `uv add [package-name]`
- Check Python path and virtual environment

**Calendar sync fails**
- Verify `credentials.json` file exists and is valid
- Check Google Calendar API is enabled