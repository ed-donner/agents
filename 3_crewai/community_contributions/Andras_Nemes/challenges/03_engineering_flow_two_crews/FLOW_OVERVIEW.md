# CrewAI Flows: a basic introduction

## Crew versus Flow

A **Crew** is a team of agents completing related tasks. A **Flow** sits one
level above crews and coordinates when work starts, what state is shared, and
what happens after each result arrives.

This challenge uses exactly two crews:

```text
                          +--> BackendCrew --> backend.py -----+
requirement + contract ---|                                   |--> run tests
                          +--> TestCrew ----> test_backend.py -+
```

The crews do not edit the same files. Both receive the same contract and return
their own result, which makes the parallel work safe and easy to follow.

## The three important Flow ideas

1. `@start()` marks work that begins when the Flow starts. This project has
   two start methods, so the backend and test crews can work in parallel.
2. `@listen(...)` starts a method after another method emits a result.
3. `and_(...)` creates a join. The integration method runs only after both
   crews have finished.

`EngineeringFlowState` is a Pydantic model containing the requirements,
contract, generated code, and results. Each branch writes a different field.

## Why the test crew uses a contract

Inspecting a backend file while another crew is changing it introduces timing
problems. This example uses contract-first development: both teams agree on
names and behavior first, so tests can be written without seeing the code.

Testing every tiny backend change would need more events or a loop. CrewAI
Flows can do that, but it is intentionally outside this beginner challenge.

## Running the Flow

Add `OPENAI_API_KEY` to the project `.env`, start Docker Desktop, then run:

```powershell
crewai install
crewai run
```

Agents are limited to 10 iterations, 300 seconds, and one retry. Generated
tests have a 60-second Docker timeout. These limits prevent accidental loops.

## Where to look

- `src/engineering_flow_two_crews/main.py`: Flow, state, starts, and join.
- `src/engineering_flow_two_crews/crews/backend_crew/`: backend crew.
- `src/engineering_flow_two_crews/crews/test_crew/`: test crew.
- `output/`: generated code and test results.

## Official documentation

- [CrewAI Flows](https://docs.crewai.com/en/concepts/flows)
- [Build Your First Flow](https://docs.crewai.com/en/guides/flows/first-flow)
- [Kickoff Crews Asynchronously](https://docs.crewai.com/en/learn/kickoff-async)
