# Flow Engineering Team

Flow Engineering Team is a CrewAI Flow that turns a product brief into a small application project. It coordinates specialist crews to design the application, create backend and frontend artifacts, and review the result. The generated files and review reports are written to a shared `sandbox/` directory.

## Goals

- Demonstrate how a CrewAI Flow can coordinate specialized crews across a multi-stage engineering workflow.
- Carry a single application brief and approved design through implementation and validation.
- Keep the generated project small, testable, and scoped to the requested behavior.
- Preserve a manifest of the brief, stage summaries, validation report, and generated artifact paths.

This is an application-generation prototype and learning example. It does not deploy the generated application or guarantee that the generated code is production-ready.

## Example business case

The default brief in `src/flow_engineering_team/main.py` is an internal trading-simulation app. Users can manage a virtual account, deposit and withdraw funds, record share purchases and sales, and review holdings, transactions, and profit or loss. It includes rules against overdrawing the account or trading shares the user cannot afford or does not own. The brief describes a fixed-price example for AAPL, TSLA, and GOOGL; it is not a live market-data integration or a real trading system.

The flow can also be used to prototype other small internal tools, such as an inventory tracker, a simple booking interface, or an account-management dashboard. These are examples of possible briefs, not additional built-in features.

## Architecture and workflow

`EngineeringAppFlow` in `src/flow_engineering_team/main.py` passes application details and each stage's outputs forward in sequence:

1. **Design** — the design crew turns the brief into an implementation specification.
2. **Backend** — the backend crew creates backend artifacts and a test report.
3. **Frontend** — the frontend crew creates a user interface and a test report. Its task configuration requires a Python UI built with Gradio.
4. **Validation** — the validation crew reviews the design and implementation artifacts together and writes a review and sign-off.

Each stage is implemented as a separate CrewAI crew with YAML-defined agents and tasks under `src/flow_engineering_team/crews/`. The crews share `sandbox/` through the read, write, and list tools in `src/flow_engineering_team/tools/sandbox_tools.py`.

```text
Product brief / trigger payload
          |
          v
Design crew -> Backend crew -> Frontend crew -> Validation crew
          \_______________________________________________/
                          sandbox/
```

The generated files are organized by stage:

```text
sandbox/
├── design/      # Initial and finalized design
├── backend/     # Backend files, summary, and test report
├── frontend/    # UI files, summary, and test report
├── validation/  # Integration review and sign-off
└── flow_manifest.json
```

The manifest is updated as the flow progresses and records the brief, stack hint, stage summaries, validation report, acceptance flag, and artifact paths. The acceptance flag is based on the validation response; it is an agent-produced review, not an automated test run or deployment approval.

## Requirements

- Python `>=3.10,<3.14`
- [uv](https://docs.astral.sh/uv/)
- An [OpenRouter](https://openrouter.ai/) API key with access to the model configured in the crew YAML files

The crew configurations currently specify `openrouter/openai/gpt-5.4-mini`. The project dependencies, including CrewAI and Gradio, are declared in `pyproject.toml` and pinned through `uv.lock`.

## Setup

From this project directory:

```bash
python -m pip install uv
uv sync --locked
cp .env.example .env
```

Add your OpenRouter key to `.env`:

```dotenv
OPENROUTER_API_KEY=your_openrouter_api_key
```

`OPENROUTER_BASE_URL` is also provided in `.env.example`; leave it blank unless you need to use a custom OpenRouter-compatible endpoint. Keep `.env` private and do not commit API keys.

## Run the flow

Start the flow using its configured project entry point:

```bash
uv run kickoff
```

To provide a custom brief, call the trigger entry point with a JSON payload:

```bash
uv run run_with_trigger '{"app_name":"Inventory Tracker","app_description":"Track items, quantities, and stock changes for a small team.","target_audience":"Operations staff","stack_hint":"FastAPI backend and a Gradio UI"}'
```

Supported payload fields are `app_name`, `app_description`, `target_audience`, and `stack_hint`. Omitted fields use the defaults in `AppBuildState`. The trigger accepts JSON as a command-line argument; quote and escape it as required by your shell.

After the flow completes, inspect the generated source files, test artifacts, reports, and `sandbox/flow_manifest.json`. The crews produce test files and reports, but this flow does not itself run the generated application's tests or launch the generated app.

## Customize

- Edit `app_description` and the default metadata in `src/flow_engineering_team/main.py`, or provide values through the trigger payload.
- Adjust crew roles and model selections in each crew's `config/agents.yaml`.
- Adjust the stage instructions and expected outputs in each crew's `config/tasks.yaml`.
- Change stage ordering or data passed between stages in `src/flow_engineering_team/main.py`.
- Change sandbox file access behavior in `src/flow_engineering_team/tools/sandbox_tools.py`.

Keep task prompts, implementation constraints, and acceptance criteria aligned when changing the workflow. For example, the frontend task currently restricts generated interfaces to Gradio.

## Limitations

- Generated files are proposals for a small application, not a secured or production deployment.
- The default trading brief uses example fixed prices and must not be used for real financial decisions or trading.
- Validation is based on generated artifact review and sign-off text. It does not execute the generated app or tests, perform security certification, or replace human review.
- Model usage requires a working OpenRouter account and may incur provider charges.
