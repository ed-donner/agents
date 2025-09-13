# AI Career Assistant

An AI-powered career assistant that represents professionals on their websites, answering questions about their background while facilitating follow-up contact for qualified opportunities. Built with a template-based architecture using OpenAI's latest structured output features and a simple prompt management system.

## Features

- **Intelligent Q&A**: Answers questions about professional background using resume, LinkedIn, and summary documents
- **GitHub Integration**: Real-time repository analysis and project showcasing
- **Job Matching**: LLM-powered job fit analysis with detailed skill assessments
- **Contact Facilitation**: Contact routing based on query type and job match quality
- **Response Evaluation**: Built-in quality control system to prevent hallucinations
- **Template-Based Prompts**: Maintainable prompt management with composition and variable substitution
- **Push Notifications**: Pushover integration for real-time alerts
- **Web Interface**: Clean Gradio-based chat interface

## Architecture

This project follows a template-based prompt architecture with clear separation of concerns:

```
personal-ai/
├── models/              # Data models & schemas
│   ├── config.py           # Configuration classes
│   ├── evaluation.py       # Response evaluation models
│   ├── job_match.py        # Job analysis models
│   └── responses.py        # Structured response models
├── prompts/             # Template-based prompt management
│   ├── chat_init.md           # Main AI assistant system prompt
│   ├── chat_base.md           # Base system prompt (for rerun)
│   ├── chat_rerun.md          # Response regeneration template
│   ├── evaluator.md           # Response evaluation prompt
│   ├── evaluator_with_github_context.md  # GitHub-enhanced evaluator
│   └── job_match_analysis.md  # Job matching analysis prompt
├── docs/               # Documentation
│   └── prompt-refactoring-plan.md  # Prompt management architecture
├── me/                 # Professional documents
│   ├── resume.pdf         # Professional resume
│   ├── linkedin.pdf       # LinkedIn profile export
│   └── summary.txt        # Professional summary
├── promptkit.py        # Template rendering engine
├── career_chatbot.py   # Main application with integrated services
└── README.md          # This documentation
```

## Prompt Management System

This application features a template-based prompt management system that separates AI prompts from Python code for better maintainability and flexibility.

### Key Components

- **`promptkit.py`**: Template rendering engine with variable substitution
- **`prompts/` directory**: All AI prompts stored as markdown templates
- **Template composition**: Complex prompts built by composing simpler templates
- **Variable substitution**: Dynamic content injection using `{variable}` syntax

### Template Features

**Variable Substitution:**
```markdown
You are an AI assistant representing {config.name}.
Current date: {current_date}
```

**Template Composition:**
```markdown
{base_evaluator_prompt}

## GitHub Tool Results:
{github_context}
```

**Conditional Logic:**
```python
# In Python code
github_tools = "Use GitHub tools for repo questions" if web_search_service else ""
vars = {"github_tools": github_tools}
```

### Prompt Templates

- **`chat_init.md`**: Main conversational AI prompt with behavioral rules
- **`evaluator.md`**: Response quality control and hallucination detection
- **`evaluator_with_github_context.md`**: Enhanced evaluator for GitHub tool responses
- **`job_match_analysis.md`**: Job matching analysis
- **`chat_rerun.md`**: Response regeneration with evaluator feedback
- **`chat_base.md`**: Base conversational prompt without evaluation context

### Benefits

- **🔧 Maintainable**: Edit prompts without touching Python code
- **📋 Version Control Friendly**: Clear diffs for prompt changes
- **🧩 Composable**: Build complex prompts from reusable components
- **🎯 Consistent**: Unified variable substitution approach
- **🧪 Testable**: Prompts can be tested independently

## Installation

### Option 1: Using uv (Recommended)

1. **Install uv (if not already installed):**
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   # or with pip: pip install uv
   ```

2. **Clone and navigate to the project:**
   ```bash
   cd personal-ai
   ```

3. **Create virtual environment and install dependencies:**
   ```bash
   uv venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   uv pip install -r requirements.txt

   # Alternative: Install using pyproject.toml
   # uv pip install -e .
   ```

### Option 2: Using pip (Traditional)

1. **Clone and navigate to the project:**
   ```bash
   cd personal-ai
   ```

2. **Create virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables:**
   Create a `.env` file in the parent directory with:
   ```env
   OPENAI_API_KEY=your_openai_api_key
   GEMINI_API_KEY=your_gemini_api_key    # For evaluation
   GITHUB_USERNAME=your_github_username  # Optional
   GITHUB_TOKEN=your_github_token        # Optional, for higher rate limits
   PUSHOVER_USER=your_pushover_user      # Optional
   PUSHOVER_TOKEN=your_pushover_token    # Optional
   ```

5. **Prepare your documents:**
   Place your professional documents in the `me/` directory:
   - `resume.pdf` - Your resume
   - `linkedin.pdf` - LinkedIn profile export
   - `summary.txt` - Professional summary

## Usage

### Basic Usage
```bash
python career_chatbot.py
```

### Programmatic Usage
```python
from models import ChatbotConfig
from career_chatbot import CareerChatbot

config = ChatbotConfig(
    name="Your Name",
    github_username="your_username"
)

chatbot = CareerChatbot(config)
chatbot.launch_interface()
```

### Prompt Customization
```python
from promptkit import render

# Custom prompt rendering
vars = {
    "config": config,
    "context": context,
    "current_date": "September 6, 2025"
}
prompt = render("prompts/chat_init.md", vars)
```

## Configuration

The `ChatbotConfig` class supports extensive customization:

```python
config = ChatbotConfig(
    name="Professional Name",
    github_username="github_user",
    resume_path="me/resume.pdf",
    linkedin_path="me/linkedin.pdf",
    summary_path="me/summary.txt",
    model="gpt-4o-mini-2024-07-18",
    evaluator_model="gemini-2.5-flash",
    job_matching_model="gpt-4o-2024-08-06",
    job_match_threshold="Good"
)
```

## AI Agent Tools

The system includes several specialized tools:

- **`record_user_details`**: Captures contact information for follow-up
- **`evaluate_job_match`**: Analyzes job fit using advanced LLM reasoning
- **`search_github_repos`**: Retrieves and analyzes GitHub repositories
- **`get_repo_details`**: Provides detailed repository information

## Job Matching

The job matching system uses a sophisticated 6-level hierarchy:

- **Very Strong** (90%+ skills): Minimal gaps, excellent fit
- **Strong** (70-89% skills): Few gaps, strong candidate
- **Good** (50-69% skills): Manageable gaps, solid fit
- **Moderate** (30-49% skills): Significant gaps, some foundation
- **Weak** (10-29% skills): Major gaps, limited relevance
- **Very Weak** (<10% skills): Complete domain mismatch

## Quality Control

Evaluation system with template-based prompts prevents hallucinations:

### Evaluation Features
- **Factual Validation**: All claims verified against source documents and GitHub tool results
- **Tool Usage Verification**: Ensures appropriate tool selection and detects missing tool calls
- **Behavioral Rules**: Enforces proper contact facilitation logic
- **Date Context Awareness**: Proper temporal validation using system date context
- **GitHub Tool Integration**: Special handling for repository data and metadata
- **Retry Mechanism**: Automatically regenerates poor responses with evaluator feedback

### Evaluation Templates
- **Base Evaluator**: Strict validation against resume/LinkedIn context
- **GitHub-Enhanced**: Accepts repository data as legitimate additional context
- **Job Matching**: Specialized evaluation for technical skill assessments

### Evaluation Process
1. **Structured Response Generation**: AI provides response with reasoning and evidence
2. **Context-Aware Evaluation**: Template-based evaluation with current date and tool context
3. **Automatic Retry**: Failed responses regenerated with specific feedback
4. **Quality Assurance**: Only validated responses reach the user

## Development

### Local Development

**With uv (Recommended):**
```bash
# Create and activate virtual environment
uv venv
source .venv/bin/activate

# Install dependencies
uv pip install -r requirements.txt

# Run the application
python career_chatbot.py

# Optional: Run with development tools
ruff check .  # Linting (if configured)
```

**With pip:**
```bash
# Install dependencies
pip install -r requirements.txt

# Run the application
python career_chatbot.py
```

### Prompt Development

Edit prompts directly in the `prompts/` directory:

```bash
# Edit main chat prompt
vim prompts/chat_init.md

# Edit evaluator prompt
vim prompts/evaluator.md

# Test changes immediately - no restart required
# Prompts are loaded fresh on each request
```

## Example Interactions

**Professional Question:**
> "What experience does this person have with robotics?"

**Job Matching:**
> "Here's a Senior Robotics Engineer position at Boston Dynamics. How well would this person fit?"

**GitHub Projects:**
> "Can you show me some of their open source work?"

## Testing

```bash
# Test the application
python career_chatbot.py

# Test prompt rendering
python -c "from promptkit import render; print('Template system works')"

# Test model imports
python -c "from models import ChatbotConfig; print('Models loaded successfully')"
```
