# Learning Path Generator

A LangGraph-powered agent that creates personalized learning paths for any topic.

## Features

- **Research**: Automatically researches topics using Wikipedia and Tavily web search
- **Curriculum Building**: Structures learning into ordered milestones with resources
- **Evaluation**: Validates the curriculum for completeness and logical ordering
- **Export**: Generates polished Markdown and PDF documents
- **Notification**: Sends the learning path to your inbox via Resend email API

## Architecture

```
┌─────────┐     ┌───────────────────┐     ┌───────────┐
│  START  │────▶│    Researcher     │────▶│ Curriculum│
└─────────┘     └───────────────────┘     │  Builder  │
                                          └───────────┘
                                                │
                                                ▼
                                          ┌───────────┐
                        ┌─────────────────│ Evaluator │
                        │                 └───────────┘
                        │ (revision)            │
                        │                       │ (approved)
                        ▼                       ▼
                  ┌───────────┐          ┌───────────────┐
                  │ Curriculum│          │   Markdown    │
                  │  Builder  │          │    Writer     │
                  └───────────┘          └───────────────┘
                                                │
                                                ▼
                                          ┌───────────┐
                                          │    PDF    │
                                          │   Writer  │
                                          └───────────┘
                                                │
                                                ▼
                                          ┌───────────┐
                                          │ Notifier  │
                                          └───────────┘
                                                │
                                                ▼
                                          ┌─────────┐
                                          │   END   │
                                          └─────────┘
```

## Project Structure

```
learning_planner/
├── app.py              # Gradio UI
├── graph.py            # LangGraph pipeline
├── state.py            # State definitions & Pydantic models
├── tools.py            # Tool implementations
├── nodes/              # Node classes
│   ├── __init__.py
│   ├── researcher.py
│   ├── curriculum_builder.py
│   ├── evaluator.py
│   ├── markdown_writer.py
│   ├── pdf_writer.py
│   └── notifier.py
├── sandbox/            # Generated outputs
└── README.md
```

## Setup

### Prerequisites

Ensure these environment variables are set in the root `.env` file:

```bash
OPENAI_API_KEY=your_openai_api_key
TAVILY_API_KEY=your_tavily_api_key
RESEND_API_KEY=your_resend_api_key  # Optional - for email notifications
```

### Run

From the project root:

```bash
uv run python 4_langgraph/community_contributions/wakanda_team_thomas/learning_planner/app.py
```

Then open http://127.0.0.1:7860 in your browser.

## Usage

1. **Enter a topic** - What you want to learn (e.g., "Kubernetes", "LangGraph")
2. **Select skill level** - Your current knowledge level
3. **Choose time commitment** - How much time you can dedicate daily
4. **Add email (optional)** - To receive the PDF directly
5. **Click Generate** - Wait for the pipeline to complete

## LangGraph Concepts Used

| Concept | Implementation |
|---------|----------------|
| **StateGraph** | Main pipeline orchestration |
| **Nodes** | 6 specialized node classes |
| **Conditional Edges** | Evaluator routing (revision vs approved) |
| **Checkpointer** | MemorySaver for persistence |
| **Structured Outputs** | Pydantic models for curriculum, evaluation |
| **Tool Integration** | Wikipedia, Tavily, File I/O, Email |

## Nodes

| Node | Purpose |
|------|---------|
| **Researcher** | Gathers topic info from Wikipedia & web |
| **CurriculumBuilder** | Creates structured milestones |
| **Evaluator** | Validates curriculum quality |
| **MarkdownWriter** | Generates formatted markdown |
| **PDFWriter** | Converts markdown to styled PDF |
| **Notifier** | Sends email with PDF attachment |

## Output Example

The generator creates:

1. **Markdown file** (`sandbox/learning_path_<topic>.md`)
2. **PDF file** (`sandbox/learning_path_<topic>.pdf`)
3. **Email** (if address provided)

## Team

**Design by M.T.Gasmyr**
