## Leadership Calibration Crew

Welcome to the **Leadership Calibration** project, powered by [crewAI](https://crewai.com).

This crew models a structured debate between two senior leadership personas:

- **Senior Architect** – focuses on technical design, scalability, and system quality.
- **Engineering Manager** – focuses on people, delivery, and business impact.

Given a topic, the crew runs a multi-step debate and produces:

- **Architect position** → `architect.md`
- **Engineering manager position** → `manager.md`
- **Final synthesized conclusion** → `conclusion.md`

You can run the crew through an interactive Gradio UI.

---

## Installation

- **Python**: requires `>=3.10,<3.14`
- **Dependencies**: managed with [UV](https://docs.astral.sh/uv/) and `pyproject.toml`

Install `uv` (once, globally):

```bash
pip install uv
```

From the project root (`3_crew/leadership_calibration`), install dependencies:

```bash
uv sync
```

Or, if you prefer the crewAI CLI workflow:

```bash
crewai install
```

Make sure your `OPENAI_API_KEY` (or other LLM provider keys) is available in the environment
or defined in a local `.env` file.

---

## Project Structure

Key components of the crew live under `src/leadership_calibration`:

- **Agents configuration**: `config/agents.yaml`  
  - `engineering_manager_agent` – senior engineering manager & technical leader  
  - `senior_architect_agent` – senior software engineer & architect

- **Tasks configuration**: `config/tasks.yaml`  
  - `architect_position_statement` → writes `output/architect.md`  
  - `engineering_manager_position_statement` → writes `output/manager.md`  
  - `final_alignment_and_resolution` → writes `output/conclusion.md`

- **Crew orchestration**: `crew.py`  
  - Defines the `LeadershipCalibration` crew and wires agents + tasks.

- **CLI entrypoints**: `main.py`  
  - Provides `run`, `train`, `replay`, `test`, and `run_with_trigger` functions.

- **Gradio app**: `app.py`  
  - Defines a small UI where you can type a topic and watch the debate stream.

Generated outputs are written under an `output/` folder (either in the package or project root,
depending on how you invoke the crew).

---

## Running the Gradio UI

The interactive web UI is defined in `src/leadership_calibration/app.py` using Gradio.
To launch it:

```bash
uv run app.py
```

Then:

1. Open the local URL printed by Gradio in your browser.
2. Enter a **debate topic** (e.g. “Should we migrate to microservices?”).
3. Click **Start Debate** to begin streaming the discussion.
4. Use **Cancel Debate** to stop an in-progress run.

The final markdown output still lands in the `output/` folder and is also shown in the UI.

---

## Customizing the Leadership Calibration

- **Agents** – edit `src/leadership_calibration/config/agents.yaml`  
  - Update roles, goals, and instructional style (`instructions` block).

- **Tasks & debate flow** – edit `src/leadership_calibration/config/tasks.yaml`  
  - Change task descriptions, expected outputs, or ordering.

- **Crew wiring & tools** – edit `src/leadership_calibration/crew.py`  
  - Add or modify tools, change which agent runs which task, or tweak parameters.

- **CLI behavior** – edit `src/leadership_calibration/main.py`  
  - Adjust default topics, input schema, or logging.

- **UI behavior** – edit `src/leadership_calibration/app.py` and `debate_runner.py`  
  - Change layout, streaming behavior, or how the debate is rendered.

---

## Support

For more about crewAI:

- **Docs**: `https://docs.crewai.com`  
- **GitHub**: `https://github.com/joaomdmoura/crewai`  
- **Discord**: `https://discord.com/invite/X4JWnZnxPb`

This project is a specialized example on top of crewAI for calibrating leadership decisions via structured debate.

