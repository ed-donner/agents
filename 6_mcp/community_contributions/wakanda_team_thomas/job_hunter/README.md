# Job Hunter - Autonomous Multi-Agent Job Hunting System

An autonomous multi-agent system for automated job hunting using OpenAI Agents SDK.

## Features

- **Resume Parsing**: Upload PDF or Word resumes for automatic skill extraction
- **Smart Matching**: Only jobs matching your profile by 90%+ are considered
- **Remote Only**: Focuses exclusively on 100% remote positions
- **Free Job Boards**: Searches RemoteOK, Remotive, and Arbeitnow
- **Observability**: Full tracing with Langfuse
- **MCP Server**: Persistent storage for jobs and profiles

## Architecture

The system uses a manager orchestration pattern with specialized agents:

1. **Resume Parser Agent**: Extracts text from PDF/DOCX files
2. **Profile Builder Agent**: Structures resume data into searchable profile
3. **Job Search Agent**: Queries multiple free job boards
4. **Job Matcher Agent**: Scores job-profile compatibility

## Setup

### Prerequisites

- Python 3.11+
- UV package manager
- OpenAI API key
- Langfuse credentials (optional but recommended)

### Installation

```bash
cd 6_mcp/community_contributions/wakanda_team_thomas/job_hunter

# Create virtual environment and install dependencies
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uv pip install -e ".[dev]"
```

### Configuration

Copy the environment template and fill in your credentials:

```bash
cp .env.example .env
```

Required environment variables:
- `OPENAI_API_KEY`: Your OpenAI API key
- `LANGFUSE_PUBLIC_KEY`: Langfuse public key (optional)
- `LANGFUSE_SECRET_KEY`: Langfuse secret key (optional)
- `LANGFUSE_HOST`: Langfuse host URL (optional)

## Usage

### Start the UI

```bash
streamlit run app/main.py
```

### Run the MCP Server

```bash
uv run python -m src.mcp_server.server
```

## Project Structure

```
job_hunter/
├── src/
│   ├── agents/          # Agent definitions
│   ├── manager/         # Orchestration logic
│   ├── mcp_server/      # MCP server
│   ├── db/              # Database models
│   ├── schemas/         # Pydantic schemas
│   ├── job_boards/      # Job board clients
│   └── utils/           # Utilities
├── app/                 # Streamlit UI
├── scheduler/           # Periodic job search
└── tests/               # Test suite
```

## Testing

```bash
pytest tests/
```

## License

MIT
