# Multimodal Agent News Summarizer

An AI-powered news summarization system that aggregates news from multiple RSS feeds, creates concise summaries using Gemini 2.5 Flash, and generates audio briefings using MiniMax TTS. Built with a modular agent-based architecture following OpenAI Agents SDK patterns.

## 🚀 Features

- **Multi-Source News Aggregation**: Concurrently fetches news from multiple RSS feeds across different topics (tech, world, business, politics, sports)
- **AI-Powered Summarization**: Uses Google's Gemini 2.5 Flash to create engaging 300-word summaries optimized for audio consumption
- **Text-to-Speech**: Converts summaries into high-quality audio files using MiniMax TTS API
- **Modern Web Interface**: Beautiful Gradio-based UI with blue theme for easy interaction
- **Agent-Based Architecture**: Modular design with separate agents for each task, following OpenAI Agents SDK patterns
- **Async/Await Support**: Fully asynchronous implementation for optimal performance

## 📋 Table of Contents

- [Architecture](#architecture)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [Project Structure](#project-structure)
- [Technologies](#technologies)
- [API Keys Required](#api-keys-required)

## 🏗️ Architecture

The project follows a modular agent-based architecture with three specialized agents:

### 1. **News Aggregator Agent**

- Fetches articles from RSS feeds concurrently
- Supports multiple news topics (tech, world, business, politics, sports)
- Aggregates up to 15 most recent articles from multiple sources

### 2. **Summarizer Agent**

- Uses Gemini 2.5 Flash for intelligent summarization
- Creates 300-word summaries optimized for 2-minute audio briefings
- Structures content with opening hook, top 3 stories, and closing

### 3. **Audio Generator Agent**

- Converts text summaries to speech using MiniMax TTS
- Generates high-quality MP3 audio files
- Uses unique filenames to prevent collisions

### Orchestrator

Coordinates the workflow between all agents, ensuring smooth data flow from aggregation → summarization → audio generation.

## 📦 Installation

### Prerequisites

- Python 3.13 or higher
- pip package manager

### Steps

1. **Clone the repository** (or navigate to the project directory):

   ```bash
   cd news_summariser
   ```

2. **Create a virtual environment**:

   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies**:

   ```bash
   pip install -e .
   ```

   Or install manually:

   ```bash
   pip install openai google-generativeai feedparser gradio aiohttp aiofiles python-dotenv requests pydantic loguru
   ```

## ⚙️ Configuration

Create a `.env` file in the project root with the following API keys:

```env
# Gemini API Configuration (for summarization)
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_BASE_URL=https://generativelanguage.googleapis.com/v1beta

# MiniMax API Configuration (for text-to-speech)
MINIMAX_API_KEY=your_minimax_api_key_here
```

### Getting API Keys

1. **Gemini API Key**:

   - Visit [Google AI Studio](https://makersuite.google.com/app/apikey)
   - Create a new API key
   - Set `GEMINI_BASE_URL` to the Gemini API endpoint

2. **MiniMax API Key**:
   - Visit [MiniMax Platform](https://www.minimaxi.com/)
   - Sign up and obtain your API key

## 🎯 Usage

### Running the Application

1. **Activate the virtual environment**:

   ```bash
   source .venv/bin/activate
   ```

2. **Run the application**:

   ```bash
   python main.py
   ```

3. **Access the web interface**:
   - The Gradio interface will launch automatically
   - Open the URL shown in the terminal (typically `http://127.0.0.1:7860`)
   - Select a news topic from the dropdown
   - Click submit to generate a summary and audio briefing

### Supported News Topics

- **Tech**: Technology news from TechCrunch, The Verge, Ars Technica
- **World**: World news from BBC and New York Times
- **Business**: Business news from BBC and CNBC
- **Politics**: Political news from New York Times and BBC
- **Sports**: Sports news from New York Times and BBC

## 📁 Project Structure

```
news_summariser/
├── agents/                      # Agent modules
│   ├── __init__.py             # Agent exports
│   ├── base.py                 # Base Agent class and function_tool decorator
│   ├── news_aggregator.py      # News aggregation agent
│   ├── summarizer.py           # Summarization agent
│   └── audio_generator.py      # Audio generation agent
├── config/                      # Configuration module
│   └── __init__.py
├── main.py                      # Main entry point (Gradio UI)
├── orchestrator.py              # Workflow orchestrator
├── pyproject.toml               # Project dependencies
├── .env                         # Environment variables (create this)
└── README.md                    # This file
```

## 🛠️ Technologies

- **Python 3.13+**: Core programming language
- **Gradio**: Web interface framework
- **OpenAI SDK**: For Gemini API integration (OpenAI-compatible endpoint)
- **aiohttp**: Asynchronous HTTP client for RSS feed fetching
- **aiofiles**: Asynchronous file operations
- **feedparser**: RSS feed parsing
- **MiniMax TTS API**: Text-to-speech conversion
- **python-dotenv**: Environment variable management

## 🔑 API Keys Required

This project requires the following API keys:

1. **GEMINI_API_KEY**: For AI-powered news summarization
2. **GEMINI_BASE_URL**: Gemini API endpoint URL
3. **MINIMAX_API_KEY**: For text-to-speech audio generation

## 🎨 Features in Detail

### Agent Pattern

Each agent follows the OpenAI Agents SDK pattern:

```python
Agent(
    name="Agent Name",
    instructions="Agent instructions",
    tools=[tool_function],
    model="gemini-2.5-flash",
)
```

### Function Tools

Tools are decorated with `@function_tool` to mark them as agent capabilities:

```python
@function_tool
async def my_tool(param: str) -> str:
    """Tool description."""
    # Implementation
    return result
```

### Async Workflow

The entire workflow is asynchronous for optimal performance:

- Concurrent RSS feed fetching
- Non-blocking API calls
- Efficient file I/O operations

## 📝 Example Output

When you select a topic and generate a summary, you'll receive:

1. **Text Summary**: A 300-word engaging summary with:

   - Opening hook
   - Top 3 stories with key details
   - Brief closing

2. **Audio File**: An MP3 file containing the audio version of the summary, perfect for listening on the go

## 🤝 Contributing

This project follows clean code principles:

- Separation of concerns (each agent in its own file)
- Type hints throughout
- Comprehensive docstrings
- Error handling
- Async/await patterns

## 📄 License

This project is open source and available for educational and personal use.

## 🙏 Acknowledgments

- **Google Gemini**: For powerful AI summarization capabilities
- **MiniMax**: For high-quality text-to-speech services
- **Gradio**: For the beautiful web interface framework
- **OpenAI**: For the Agents SDK pattern inspiration

---

**Note**: Make sure to keep your `.env` file secure and never commit it to version control. The `.gitignore` file is configured to exclude it automatically.
