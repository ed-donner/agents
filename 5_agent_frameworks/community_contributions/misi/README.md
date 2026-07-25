# Dynamic AutoGen Agent Creation

This contribution explores AutoGen's dynamic runtime behavior by having one agent create, register, and message other agents.

## What Changed

- `creator.py` defines a `Creator` agent that asks an AgentChat assistant to write a new Python module.
- Each generated module defines an `Agent` class that inherits from AutoGen Core `RoutedAgent` and wraps an AutoGen AgentChat `AssistantAgent`.
- The Creator writes each generated module beside the template, imports or reloads it, and registers the new `Agent` type with the distributed gRPC runtime.
- The Creator can also create a new version of itself when asked for a filename such as `creator1.py`.
- `world.py` plans the Creator switch points up front using `CHANCES_THAT_I_CHANGE_CREATOR = 0.5`.
- The Creator chain is still created sequentially, but each Creator's planned Agent batch starts as soon as that Creator exists.
- `creator.py` exposes `read_creator_template` as an AgentChat tool so the Creator can read its own source code before writing a replica.
- `creator.py` normalizes generated code so all `OpenAIChatCompletionClient` calls keep using `gpt-4o-mini`.
- `messages.py` now tracks the names of agents that have actually been registered, so created agents can select live peers by name.
- `agent.py` keeps the collaboration behavior in the template: agents create a commercial business idea for Agents, then ask one registered peer to refine it.
- `CHANCES_THAT_I_BOUNCE_IDEA_OFF_ANOTHER` was changed from `0.5` to `1.0` so the demo reliably shows created agents messaging each other whenever a registered peer exists.

## Why

The goal is to demonstrate that AutoGen agents do not need to be fully known ahead of time. A running `Creator` agent can produce Python code, load that code as a module, register the new agent with the runtime, and immediately send messages to it.

The registered-agent list avoids choosing peers just because a matching `agent*.py` file exists. That matters because a file can exist before its agent has been registered with the runtime. The template also limits peer refinement to the initial idea request, so collaboration produces a single handoff instead of an endless message loop.

The collaboration probability is deliberately `1.0` rather than `0.5`. With `0.5`, a run could create agents but skip peer messaging by chance, which makes the main demonstration less clear. The initial-request guard keeps that deterministic collaboration from becoming an infinite back-and-forth between agents.

The creator-replication path is tool-based rather than hard-coding the source text into the prompt. The `read_creator_template` tool reads the module file through `__file__`, so a generated creator can read its own source after it has been written to `creatorN.py`. That lets each Creator make a slightly changed replica while keeping the core ability to create and register normal agents.

Creator changes are intentionally probabilistic. `world.py` rolls `CHANCES_THAT_I_CHANGE_CREATOR` across the planned Agent slots before creating the Agents. For example, with 20 Agents, the plan might assign Agents 1-2 to the original Creator, Agents 3-8 to `creator1`, Agents 9-17 to `creator2`, and Agents 18-20 to `creator3`.

The Creator chain still has to be created in order because `creator2` depends on `creator1`, and so on. `world.py` pipelines the work: it starts the current Creator's planned Agent batch, then creates the next Creator while those Agent tasks are already running. At the end it waits for all Agent tasks with `asyncio.gather`.

## Main Flow

1. `world.py` starts a distributed gRPC runtime.
2. `world.py` registers the `Creator` agent.
3. The Creator receives filenames such as `agent1.py`.
4. The Creator generates Python code from the `agent.py` template.
5. The Creator writes, imports, and registers the new module's `Agent` class.
6. The new agent generates a commercial Agentic AI business idea.
7. If another created agent is registered, it refines the idea by name.
8. `world.py` saves the resulting idea as `ideaN.md`.
9. `world.py` precomputes the Creator-change schedule for all Agent slots.
10. The active Creator's planned Agent batch is started immediately.
11. The next `creatorN.py` is created while already-started Agent tasks continue running.
12. `world.py` waits for all Agent tasks to finish.
