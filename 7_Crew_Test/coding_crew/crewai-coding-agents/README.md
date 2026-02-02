# 🤖 CrewAI Coding Agents

AI-powered coding agent ecosystem using CrewAI for automated software development.

## 📋 Overview

This project uses CrewAI to create an intelligent agent system that can:
- Analyze project requirements
- Design system architecture
- Break down projects into tasks
- Generate code for multiple languages/frameworks
- Create infrastructure configurations
- Set up CI/CD pipelines
- Generate tests
- Create documentation

## 🏗️ Project Structure

```
crewai-coding-agents/
├── agents/              # AI agent definitions
│   ├── team_manager.py
│   ├── analyst.py
│   ├── backend_engineers.py
│   ├── frontend_engineers.py
│   ├── devops_engineer.py
│   ├── db_engineer.py
│   └── qa_engineer.py
├── crews/               # Crew orchestration
│   ├── analysis_crew.py
│   └── development_crew.py
├── tasks/               # Task definitions
├── tools/               # Agent tools
│   ├── code_tools.py
│   ├── infrastructure_tools.py
│   ├── cicd_tools.py
│   └── database_tools.py
├── models/              # Data models
├── config/              # Configuration
├── workflows/           # Workflow orchestration
├── templates/           # Code templates
└── output/              # Generated outputs
```

## 🚀 Quick Start

### Prerequisites

- Python 3.10-3.12
- OpenAI API Key (or other LLM provider)

### Installation

1. **Clone and navigate to the project:**
```bash
cd crewai-coding-agents
```

2. **Set up Python environment with uv:**
```bash
# Install uv if not already installed
curl -Ls https://astral.sh/uv/install.sh | sh

# Create virtual environment
uv venv .venv-uv --python 3.12

# Activate environment
source .venv-uv/bin/activate  # On macOS/Linux
# or
.venv-uv\Scripts\activate     # On Windows

# Install dependencies
uv pip install 'crewai[tools]==0.80.0'
uv pip install -r requirements.txt
```

3. **Configure environment:**
```bash
cp .env.example .env
# Edit .env and add your API keys
```

### Usage

#### Using CrewAI CLI:

```bash
# Run the demo analysis
crewai run

# Check status
python main.py status
```

#### Using Python directly:

```bash
# Run analysis only
python main.py analyze --backend python --frontend react

# Run full development workflow
python main.py develop --output-dir ./my-project

# Run demo
python main.py demo
```

## 🎯 Features

### Supported Technologies

**Backend:**
- Python (FastAPI, Django)
- Go (Gin, Echo)
- Node.js (Express, NestJS)
- C# (.NET)

**Frontend:**
- React (with SSR via Next.js)
- Angular
- Vue.js

**Databases:**
- PostgreSQL
- MySQL
- MongoDB
- Redis

**Infrastructure:**
- AWS (ECS, EKS, RDS, Lambda, etc.)
- Kubernetes
- Docker
- Terraform

**CI/CD:**
- GitHub Actions
- GitLab CI
- Jenkins

## 📝 Example Workflow

```python
from models.requirements import ComplexStackRequest
from workflows import ProjectWorkflow

# Define your project
request = ComplexStackRequest(
    project_name="My E-Commerce Platform",
    description="Modern e-commerce with microservices",
    backend_language="python",
    backend_framework="fastapi",
    frontend_framework="react",
    # ... more configuration
)

# Run workflow
workflow = ProjectWorkflow()
result = workflow.execute(request)
```

## 🔧 Configuration

Key configuration in `.env`:

```bash
# LLM Provider
OPENAI_API_KEY=your-key-here
DEFAULT_LLM_MODEL=gpt-4-turbo-preview

# CrewAI Settings
CREWAI_VERBOSE=true
CREWAI_MEMORY=true

# Output Settings
OUTPUT_DIR=./output
LOG_LEVEL=INFO
```

## 🧪 Development

### Running Tests

```bash
pytest tests/
pytest tests/ --cov=. --cov-report=html
```

### Project Structure Conventions

- Each agent has specific responsibilities
- Tasks are defined separately from agents
- Tools are reusable across agents
- All generated code goes to `output/`

## 📊 Agents Overview

| Agent | Role | Responsibilities |
|-------|------|-----------------|
| Team Manager | Orchestration | Coordinates all agents, manages workflow |
| Analyst | Analysis | Analyzes requirements, tracks progress |
| Backend Engineers | Development | Generates backend code (Python, Go, etc.) |
| Frontend Engineers | Development | Generates frontend code (React, Angular) |
| DevOps Engineer | Infrastructure | Creates Docker, K8s, CI/CD configs |
| DB Engineer | Database | Designs schemas, creates migrations |
| QA Engineer | Testing | Generates tests, ensures quality |

## 🎨 Output Examples

The system generates:
- Complete project structures
- API endpoints and services
- Database schemas and migrations
- Docker and Kubernetes configs
- CI/CD pipelines
- Test suites
- Documentation

## 📚 Documentation

For detailed documentation, see:
- [Architecture Design](docs/architecture.md) (to be created)
- [Agent Guide](docs/agents.md) (to be created)
- [Tool Reference](docs/tools.md) (to be created)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests
5. Submit a pull request

## 📄 License

This project is part of The Complete AI Agent Course.

## 🙏 Acknowledgments

- Built with [CrewAI](https://github.com/joaomdmoura/crewai)
- Uses [LangChain](https://github.com/langchain-ai/langchain)
- Powered by OpenAI GPT models

## 🐛 Troubleshooting

### Common Issues

**1. Module not found errors:**
```bash
# Reinstall dependencies
uv pip install --force-reinstall -r requirements.txt
```

**2. API Key errors:**
```bash
# Check your .env file
cat .env | grep API_KEY
```

**3. Python version issues:**
```bash
# Ensure Python 3.10-3.12
python --version
# Recreate venv if needed
rm -rf .venv-uv
uv venv .venv-uv --python 3.12
```

## 📞 Support

For issues and questions:
- Open an issue on GitHub
- Check existing documentation
- Review example projects in `examples/`

---

**Last Updated:** December 16, 2025
**Version:** 0.1.0
