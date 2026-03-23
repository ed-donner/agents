# Learning Path Generator

A LangGraph-powered agent that creates personalized learning paths for any topic.

## Features

- **Research**: Automatically researches topics, prerequisites, and key concepts
- **Curriculum Building**: Structures learning into ordered milestones with resources
- **Evaluation**: Validates the curriculum for completeness and logical ordering
- **Export**: Generates polished Markdown and PDF documents
- **Notification**: Sends the learning path to your inbox via email

## Architecture

```
Researcher → Curriculum Builder → Evaluator → Markdown Writer → PDF Writer → Notifier
                    ↑                 │
                    └─────────────────┘
                      (if incomplete)
```

## Setup

Ensure the following keys are set in your root `.env` file:

- `OPENAI_API_KEY` — For LLM capabilities
- `SERPER_API_KEY` — For web search (get key at serper.dev)
- `RESEND_API_KEY` — For email notifications (get key at resend.com)

Run from the `learning_planner` directory:
```bash
python app.py
```

## Usage

1. Enter the topic you want to learn
2. Provide your email address
3. Select your current skill level
4. Choose your time commitment
5. Click "Generate" and wait for your personalized learning path

## Output

- Markdown file saved to `sandbox/`
- PDF file saved to `sandbox/`
- Email sent to your inbox with PDF attachment

## Team

Wakanda Team: Mougang T. Gasmyr
