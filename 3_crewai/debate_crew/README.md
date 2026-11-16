# DebateCrew — Multi-Agent AI Debate System

## Overview

DebateCrew is a multi-agent AI application built with CrewAI. It simulates a structured debate in which two AI agents argue opposing sides of a motion and a third AI agent evaluates their arguments to produce a final verdict.

The project demonstrates how multiple specialized AI agents can collaborate through sequential tasks to analyze a topic from different perspectives.

## Features

- **Proposer Agent:** Presents arguments in favor of the given motion.
- **Opposer Agent:** Presents arguments against the given motion.
- **Judge Agent:** Evaluates both arguments and determines which side makes the stronger case.
- **Sequential Workflow:** Executes the proposal, opposition, and judging tasks in order.
- **Automated Verdict:** Saves the final debate decision to `debate_verdict.md`.
- **Configurable Debate Motion:** Allows the debate topic to be changed through the project inputs.

## How It Works

DebateCrew follows a three-stage workflow:

1. **Propose:** The proposer develops a convincing argument supporting the motion, including three arguments or examples.
2. **Oppose:** The opposer develops a convincing counterargument against the motion, including three counterarguments or examples.
3. **Judge:** The judge evaluates both sides, compares their logic, relevance, reasoning, and evidence, and selects the stronger argument.

The workflow uses CrewAI's sequential process, ensuring that the tasks execute in the configured order.

## Technology Stack

- **Python:** Application programming language.
- **CrewAI:** Multi-agent orchestration framework.
- **YAML:** Agent and task configuration.
- **UV:** Python project and dependency management.
- **OpenAI API:** Language model provider.
- **Markdown:** Final debate verdict output.

## Project Structure

```text
debate_crew/
├── src/
│   └── debate_crew/
│       ├── __init__.py
│       ├── main.py
│       ├── crew.py
│       └── config/
│           ├── agents.yaml
│           └── tasks.yaml
├── .env
├── .gitignore
├── pyproject.toml
├── uv.lock
├── README.md
└── debate_verdict.md
```

**Important:** The `.env` file contains configuration and API credentials. Keep it private and do not commit it to a public repository.

The generated `debate_verdict.md` file appears after a successful run. Other files may vary depending on your local project configuration.

## Prerequisites

Before running the project, make sure you have:

- Python 3.10–3.13.
- UV installed.
- An OpenAI API key with access to the configured model.
- A terminal and a code editor such as Cursor.

## Installation

### 1. Open the project directory

Navigate to the DebateCrew project:

```bash
cd /Users/aqeelaimran/projects/projects/agents/3_crewai/debate_crew
```

If you are already inside the `debate_crew` directory, you can skip this step.

### 2. Install dependencies

Run:

```bash
uv sync
```

This installs the dependencies specified in `pyproject.toml` and synchronizes the project's environment.

### 3. Configure environment variables

Create or update the project's `.env` file with your own API credentials and any required model configuration.

Example structure:

```dotenv
OPENAI_API_KEY=your_openai_api_key
```

Replace the placeholder with your actual API key. Never publish or share the key.

Ensure that the configured language model is supported by your CrewAI and LiteLLM setup.

## Running the Project

Run DebateCrew from the project root:

```bash
uv run debate_crew
```

This command runs DebateCrew using the entry point configured in `pyproject.toml`. The proposer and opposer generate their arguments, and the judge evaluates both sides and writes the final verdict to `debate_verdict.md`.

The crew runs three tasks in sequence: the proposer presents the case in favor, the opposer presents the case against, and the judge evaluates both arguments. The final verdict is saved to `debate_verdict.md`.

## Changing the Debate Motion

To change the topic, open:

```text
src/debate_crew/main.py
```

Find the `inputs` configuration and update the `motion` value.

For example:

```python
inputs = {
    "motion": "Artificial intelligence will improve education."
}
```

You can replace the motion with another topic suitable for structured discussion.

Examples:

- Artificial intelligence will improve education.
- Remote work is better than office-based work.
- Social media has a positive impact on society.
- Renewable energy should replace fossil fuels as quickly as possible.

Keep the motion clear and specific so both agents can develop relevant arguments.

## Customizing Agents and Tasks

### Agent configuration

Edit:

```text
src/debate_crew/config/agents.yaml
```

This file defines each agent's role, goal, backstory, and language model.

The project includes:

- `proposer`
- `opposer`
- `judge`

When editing the configuration, ensure the agent names match the names referenced in `crew.py`.

### Task configuration

Edit:

```text
src/debate_crew/config/tasks.yaml
```

This file defines the instructions and expected output for each task.

You can improve the debate by asking agents to:

- Use verifiable facts and concrete examples.
- Identify assumptions and weaknesses.
- Distinguish evidence from opinion.
- Address the strongest opposing arguments.
- Explain the criteria used to evaluate the debate.

If factual accuracy is important, verify important claims against reliable sources. AI-generated arguments can contain errors or unsupported statements.

## Output

After a successful run, the judge's verdict is saved to:

```text
debate_verdict.md
```

The output is intended to summarize the debate decision and explain the reasoning behind the selected side.

Open this file in Cursor or another Markdown editor to review the result.

The verdict's exact structure and level of detail depend on the task instructions and the model's response.

## Troubleshooting

### 1. Missing agent configuration

If you encounter a `KeyError` for `proposer`, `opposer`, or `judge`, check that `src/debate_crew/config/agents.yaml` contains all three matching agent names.

### 2. API authentication errors

Check that the API key is configured correctly in the environment and that the account has access to the selected model.

Do not print API keys in the terminal or include them in error reports.

### 3. Dependency or environment errors

Run:

```bash
uv sync
```

Then retry:

```bash
uv run debate_crew
```

### 4. Missing output file

Check the terminal output for task failures and confirm that the configured output file path is `debate_verdict.md`.

### 5. Model configuration errors

Confirm that the model specified in `agents.yaml` is supported by the installed CrewAI and LiteLLM dependencies and that your API account can use it.

## Learning Objectives

This project provides practical experience with:

- Designing specialized AI agents.
- Defining agent roles, goals, and backstories.
- Configuring agents and tasks with YAML.
- Orchestrating multi-agent workflows.
- Passing task context between agents.
- Using sequential task execution.
- Generating and reviewing structured AI output.
- Managing Python dependencies with UV.

## Limitations

- The quality of the verdict depends on the instructions, model, and arguments generated.
- The agents may produce unsupported or inaccurate claims.
- A judge agent does not guarantee a neutral or factually correct conclusion.
- The current workflow does not independently guarantee citations or external fact-checking.
- API access and usage may incur costs.

## Future Improvements

Possible future enhancements include:

- Adding reliable source retrieval and citations.
- Fact-checking important claims before the judge reaches a verdict.
- Introducing a scoring rubric for evidence, logic, relevance, and rebuttals.
- Saving debate history and structured evaluation results.
- Supporting user-provided motions through command-line input.
- Adding automated tests for configuration and workflow behavior.
- Exporting results to HTML or PDF.

## License

No license has been specified for this project. Add an appropriate license before distributing it publicly.

## Acknowledgments

Built as a learning project using the CrewAI multi-agent framework and the concepts of agent specialization, task orchestration, and collaborative AI workflows.
