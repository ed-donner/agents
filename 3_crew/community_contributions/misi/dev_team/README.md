# DevTeam Crew

This project is a CrewAI-based software delivery crew that generates a multi-module Python application from a high-level requirements prompt.

Unlike the original static scaffold, this version does not hardcode the backend module tasks in YAML. Instead, the crew runs in two phases:

1. The `engineering_lead` designs the architecture at runtime.
2. Python code in `src/dev_team/crew.py` dynamically creates the implementation, frontend, and test tasks from that design.

## Architecture

```text
+---------------------------+
| main.py                   |
| requirements string       |
+---------------------------+
             |
             v
+---------------------------+
| EngineeringTeam.kickoff() |
+---------------------------+
             |
             v
+---------------------------+
| Design Crew               |
| agent: engineering_lead   |
+---------------------------+
             |
             v
+---------------------------+
| design_task               |
| output: ApplicationDesign |
+---------------------------+
             |
             v
+---------------------------+
| Normalize design          |
| - clean file names        |
| - clean dependencies      |
| - validate module count   |
+---------------------------+
             |
             v
+---------------------------+
| Order modules             |
| TopologicalSorter(graph)  |
+---------------------------+
             |
             v
+---------------------------+
| Generate runtime tasks    |
| - backend module tasks    |
| - app.py task             |
| - test task per module    |
+---------------------------+
             |
             v
+---------------------------+
| Implementation Crew       |
| backend_engineer          |
| frontend_engineer         |
| test_engineer             |
+---------------------------+
             |
             v
+---------------------------+
| output/*.py               |
| generated modules, app,   |
| and per-module tests      |
+---------------------------+
```

## How It Works

### 1. Requirements input

The requirements live in [src/dev_team/main.py](src/dev_team/main.py). That file passes:

```python
inputs = {"requirements": requirements}
```

into:

```python
EngineeringTeam().kickoff(inputs=inputs)
```

### 2. Design phase

The first phase is implemented in [src/dev_team/crew.py](src/dev_team/crew.py).

`EngineeringTeam.kickoff()` first calls `_kickoff_design_crew(inputs)`.

That method creates a single CrewAI `Task` in Python for the `engineering_lead`. The task asks the agent to:

- decide which backend modules should exist,
- define classes and functions for each module,
- define dependencies between modules,
- explain how the modules collaborate,
- describe how `app.py` should use the backend modules together.

The design task uses `output_pydantic=ApplicationDesign`, so the lead returns structured data instead of free-form text.

### 3. Structured design model

The architecture is captured in two Pydantic models in [src/dev_team/crew.py](src/dev_team/crew.py):

- `ModuleDesign`
- `ApplicationDesign`

`ModuleDesign` contains:

- `file_name`
- `purpose`
- `classes`
- `functions`
- `dependencies`
- `interaction_contracts`

`ApplicationDesign` contains:

- `architecture_overview`
- `shared_data_models`
- `backend_modules`
- `frontend_summary`

This makes the runtime task generation much more reliable than parsing markdown.

### 4. Design normalization

After the design crew finishes, `_normalize_design()` cleans the result before task generation.

It:

- normalizes module filenames to a clean `*.py` format,
- normalizes dependency names the same way,
- removes self-dependencies,
- deduplicates repeated modules,
- enforces that the design contains multiple backend modules.

This protects the dynamic flow from minor agent inconsistencies such as returning `auth` in one place and `auth.py` in another.

### 5. Dependency ordering

`_order_modules()` builds a dependency graph from the designed modules and uses:

```python
list(TopologicalSorter(graph).static_order())
```

to get a dependency-safe module order.

That means if one generated module depends on another, the dependency module task is created first and can be passed as CrewAI task context to the dependent module task.

If the design produces cyclic dependencies, the code raises an error instead of creating an invalid task graph.

### 6. Runtime task generation

This is the core change.

`_build_runtime_tasks()` dynamically creates CrewAI `Task` objects in Python based on the `ApplicationDesign`.

It generates:

- one backend implementation task per designed backend module,
- one `app.py` frontend task,
- one test task per designed backend module.

Each backend task:

- writes to `output/<module_name>.py`,
- is assigned to `backend_engineer`,
- receives dependency module tasks as `context`.

The frontend task:

- writes to `output/app.py`,
- is assigned to `frontend_engineer`,
- receives all backend module tasks as `context`.

Each test task:

- writes to `output/test_<module>.py`,
- is assigned to `test_engineer`,
- receives the related module task and its dependency tasks as `context`.

So the number of backend and test tasks is determined at runtime by the engineering lead's design.

### 7. Implementation phase

Once the runtime tasks are generated, `EngineeringTeam.kickoff()` creates a second CrewAI `Crew` with:

- `backend_engineer`
- `frontend_engineer`
- `test_engineer`

That crew then executes the dynamically created task list sequentially.

## Why The Tasks Are Not In `tasks.yaml`

The project still keeps:

- [src/dev_team/config/agents.yaml](src/dev_team/config/agents.yaml)
- [src/dev_team/config/tasks.yaml](src/dev_team/config/tasks.yaml)

But `tasks.yaml` is now only a note explaining that tasks are created dynamically in Python.

This is intentional.

If the tasks were declared statically in YAML, we would have to predefine the module list ahead of time. That would contradict the goal of letting `design_task` decide the modules, classes, and dependencies dynamically at runtime.

## Key Files

- [src/dev_team/main.py](src/dev_team/main.py): entry point and requirements input
- [src/dev_team/crew.py](src/dev_team/crew.py): design models, design kickoff, normalization, dependency ordering, and dynamic task generation
- [src/dev_team/config/agents.yaml](src/dev_team/config/agents.yaml): agent goals and roles
- [src/dev_team/config/tasks.yaml](src/dev_team/config/tasks.yaml): documentation note that task generation happens at runtime

## LLM Configuration

The agents are currently configured in [src/dev_team/config/agents.yaml](src/dev_team/config/agents.yaml) to use:

```text
ollama/kimi-k2.5:cloud
```

This LLM setting is defined for all project agents:

- `engineering_lead`
- `backend_engineer`
- `frontend_engineer`
- `test_engineer`

## Running The Project

From the project root:

```bash
crewai run
```

The run will:

1. ask the engineering lead to design the system,
2. convert that design into runtime tasks,
3. generate backend modules,
4. generate `app.py`,
5. generate one test file per backend module.

## Validation Notes

The current implementation was statically validated with:

```bash
./.venv/bin/python -m py_compile src/dev_team/main.py src/dev_team/crew.py
```

and YAML parsing checks for the config files.

The full live crew execution still depends on the configured model and runtime environment.
