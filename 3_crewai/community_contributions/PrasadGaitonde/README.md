# GlobalClimateModelingLocalMitigation Crew

Welcome to the GlobalClimateModelingLocalMitigation Crew project, powered by [crewAI](https://crewai.com). This template is designed to help you set up a multi-agent AI system with ease, leveraging the powerful and flexible framework provided by crewAI. Our goal is to enable your agents to collaborate effectively on complex tasks, maximizing their collective intelligence and capabilities.

## Installation

Ensure you have Python >=3.10 <3.14 installed on your system. This project uses [UV](https://docs.astral.sh/uv/) for dependency management and package handling, offering a seamless setup and execution experience.

First, if you haven't already, install uv:

```bash
pip install uv
```

Next, navigate to your project directory and install the dependencies:

(Optional) Lock the dependencies and install them by using the CLI command:
```bash
crewai install
```
### Customizing

**Add your `OPENAI_API_KEY` into the `.env` file**

- Modify `src/global_climate_modeling_local_mitigation/config/agents.yaml` to define your agents
- Modify `src/global_climate_modeling_local_mitigation/config/tasks.yaml` to define your tasks
- Modify `src/global_climate_modeling_local_mitigation/crew.py` to add your own logic, tools and specific args
- Modify `src/global_climate_modeling_local_mitigation/main.py` to add custom inputs for your agents and tasks

## Running the Project

To kickstart your crew of AI agents and begin task execution, run this from the root folder of your project:

```bash
$ crewai run
```

This command initializes the global_climate_modeling_local_mitigation Crew, assembling the agents and assigning them tasks as defined in your configuration.

This example, unmodified, will run the create a `report.md` file with the output of a research on LLMs in the root folder.

## Understanding Your Crew

The global_climate_modeling_local_mitigation Crew is composed of multiple AI agents, each with unique roles, goals, and tools. These agents collaborate on a series of tasks, defined in `config/tasks.yaml`, leveraging their collective skills to achieve complex objectives. The `config/agents.yaml` file outlines the capabilities and configurations of each agent in your crew.

## Support

For support, questions, or feedback regarding the GlobalClimateModelingLocalMitigation Crew or crewAI.
- Visit our [documentation](https://docs.crewai.com)
- Reach out to us through our [GitHub repository](https://github.com/joaomdmoura/crewai)
- [Join our Discord](https://discord.com/invite/X4JWnZnxPb)
- [Chat with our docs](https://chatg.pt/DWjSBZn)

Let's create wonders together with the power and simplicity of crewAI.
==========================================================================================================
🧩 The Challenge
Global climate change modeling & localized mitigation planning
— specifically, creating an open, continuously updated system that predicts regional climate impacts and generates actionable engineering/urban plans to adapt or reverse damage.

👥 The 5-Agent Crew (Role → Focus)
1. Team Lead (Chief Architect & Strategist)
Role: Sets project priorities, breaks down high-level goals into tasks, manages inter-agent handoffs, resolves conflicts, and ensures final deliverables align with human values & scientific accuracy.

In Crew AI terms: The orchestrator – uses Process.hierarchical or custom routing logic.

2. Data Engineer Agent
Role: Ingests, cleans, and fuses data from climate satellites, IoT sensors, historical weather, carbon flux models, and socio-economic datasets. Handles versioning and anomaly detection.

Output: Unified data pipelines + flagged inconsistencies.

3. Climate Modeling Agent
Role: Runs or interfaces with existing physics-based climate models (e.g., reduced-order versions of CMIP6) and ML surrogates to project temperature, sea level, extreme events at 10km resolution.

Output: Probabilistic forecasts with uncertainty ranges.

4. Impact & Risk Agent
Role: Translates modeling outputs into local risks: crop failure, flood zones, energy demand spikes, health outcomes, supply chain disruptions. Uses economic & demographic layers.

Output: Risk heatmaps + time-series of critical thresholds (e.g., “city X will exceed wet-bulb 35°C by 2035”).

5. Solution Architect Agent
Role: Proposes engineered or nature-based solutions tailored to specific regions: green infrastructure, renewable microgrid placement, building retrofits, managed retreat plans, carbon removal feasibility.

Output: Concrete, prioritized intervention plans with cost/benefit and implementation steps.

🔁 Workflow Example (Crew AI in action)
Team Lead defines a region (e.g., Mekong Delta) and goal: “Plan for 2050 salinity intrusion & flooding.”

Data Engineer fetches and validates required datasets.

Climate Modeling Agent runs downscaled simulations.

Impact Agent maps risks to agriculture, fresh water, settlements.

Solution Architect drafts a combo of floating agriculture, levee redesign, and early warning systems.

Team Lead checks coherence, requests revisions from any agent, then compiles final report + interactive map.