# Deep Research Chat Workflow with Clarifications

A research workflow system that implements the planner, search agents, and writer as tools and leaves it up to the research_manager to carry out the workflow rather than implementing it in code.

## Key Features

- **Tool-based Architecture**: Implements planner, search agents, and writer as tools, allowing the research_manager to orchestrate the workflow dynamically
- **Chat-style Clarifications**: Supports clarifications in a chat-style workflow that allows for clarifications to clarifications
- **State Management**: Uses the SQLLiteSession feature of the OpenAIAgent SDK to maintain state in the chat-style workflow, so the frontend only needs to push user responses vs. the entire history on each iteration
- **No Email Agent**: Eliminated the email_agent for the sake of simplicity

## Requirements

**Note**: SQLLiteSession requires a version of the `openai-agents` package >= 0.2.0


