# Week 8: Code Agents

## What you'll build
A fully autonomous code agent that writes Python functions, executes them in a sandboxed subprocess, runs pytest against them, reads the failure output, and iterates until all tests pass — with no human in the loop.

## Learning objectives
By the end of this week you can:
- Execute arbitrary code safely inside a subprocess sandbox
- Build the write → run → read-error → fix → loop pattern
- Integrate Git: read a repo, open a branch, commit a passing fix
- Chain AST analysis so the agent understands code structure before editing
- Cap iterations and cost to prevent infinite loops

## Labs

| Lab | Topic | Key pattern |
|-----|-------|-------------|
| `1_lab1.ipynb` | Sandbox executor | Subprocess isolation, timeout, captured stderr |
| `2_lab2.ipynb` | Test-driven fix loop | Agent writes code, pytest validates, loop until green |
| `3_lab3.ipynb` | AST-aware editing | Agent reads AST before patching — avoids breaking callers |
| `4_lab4.ipynb` | Git-integrated agent | Read repo → branch → commit → PR summary |

## App
`app.py` — Gradio UI wrapping the full code agent. Paste a failing test, watch the agent make it pass.

## Dependencies
Additional packages needed on top of the base environment:
```
pip install gitpython astroid pytest
```

## Setup
Copy `.env.example` to `.env` and add your `OPENAI_API_KEY`.  
No external services required — everything runs locally.

## Cost estimate
~$0.05–0.20 per bug-fix run (GPT-4o-mini for iteration, GPT-4o for hard cases).
