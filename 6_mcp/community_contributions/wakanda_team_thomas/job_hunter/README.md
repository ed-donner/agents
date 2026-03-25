# Job Hunter - Autonomous Multi-Agent Job Hunting System

An autonomous multi-agent system for automated job hunting using OpenAI Agents SDK.

## Features

- **Resume Parsing**: Upload PDF or Word resumes for automatic skill extraction
- **Smart Matching**: Only jobs matching your profile by 90%+ are considered
- **100% Remote Worldwide**: Focuses exclusively on fully remote positions
- **Free Job Boards**: Searches RemoteOK, Remotive, and Arbeitnow
- **Observability**: Full tracing with Langfuse
- **MCP Server**: Persistent storage for jobs and profiles
- **Scheduled Searches**: Automatic periodic job searches

## Architecture

The system uses a manager orchestration pattern with specialized agents:

1. **Resume Parser Agent**: Extracts text and structures data from PDF/DOCX
2. **Profile Builder Agent**: Creates searchable profile from resume data
3. **Job Search Agent**: Queries multiple free job boards in parallel
4. **Job Matcher Agent**: Hybrid scoring (rule-based + LLM semantic analysis)

## Setup

### Prerequisites

- Python 3.11+
- UV package manager
- OpenAI API key
- Langfuse credentials (optional)

### Installation

```bash
cd 6_mcp/community_contributions/wakanda_team_thomas/job_hunter

# Create virtual environment and install dependencies
uv venv
source .venv/bin/activate
uv pip install -e ".[dev]"
```

### Configuration

```bash
cp .env.example .env
# Edit .env with your credentials
```

Required:
- `OPENAI_API_KEY`: Your OpenAI API key

Optional:
- `LANGFUSE_PUBLIC_KEY`: Langfuse public key
- `LANGFUSE_SECRET_KEY`: Langfuse secret key
- `LANGFUSE_HOST`: Langfuse host URL

## Usage

### Streamlit UI

```bash
uv run streamlit run app/main.py
```

### CLI

```bash
# Test text extraction
uv run python app.py extract ~/resume.pdf

# Test job board search
uv run python app.py search python django aws

# Full workflow (parse resume, build profile, search, match)
uv run python app.py hunt ~/resume.pdf

# Search for existing profile
uv run python app.py hunt-search 1 python backend
```

### MCP Server

```bash
uv run python -m src.mcp_server.server
```

### Scheduler (background job search)

```bash
uv run python -m scheduler.job_scheduler
```

## Project Structure

```
job_hunter/
├── src/
│   ├── agent_workers/   # OpenAI Agent definitions
│   │   ├── resume_parser.py
│   │   ├── profile_builder.py
│   │   ├── job_search.py
│   │   └── job_matcher.py
│   ├── manager/         # Hunt orchestration
│   ├── mcp_server/      # MCP tools for jobs/profiles
│   ├── db/              # SQLAlchemy models
│   ├── schemas/         # Pydantic schemas
│   ├── job_boards/      # API clients
│   └── utils/           # Extractors, scoring
├── app/                 # Streamlit UI
│   └── main.py
├── scheduler/           # APScheduler
├── tests/               # Test suite
├── app.py               # CLI entry point
└── pyproject.toml
```

## Workflow

1. **Upload Resume** → Extract text from PDF/DOCX
2. **Parse Resume** → LLM structures data (skills, experience, education)
3. **Build Profile** → Save to SQLite database
4. **Search Jobs** → Query RemoteOK, Remotive, Arbeitnow
5. **Match Jobs** → Rule-based scoring + LLM semantic analysis
6. **Save Matches** → Store 90%+ matches in database
7. **Track Progress** → Update job application status

## License

MIT
