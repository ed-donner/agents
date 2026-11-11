# Week 3 - CrewAI

A higher-level, config-driven framework: you describe a *team* of role-playing agents and the
tasks they pass between each other.

- **Primitives:** **`Agent`** (role / goal / backstory / llm / tools), **`Task`** (description /
  expected_output / agent), **`Crew`** (agents + tasks + process), **`Process`**
  (`sequential` or `hierarchical`).
- **The idiomatic layout** is config-as-data: `agents.yaml` + `tasks.yaml` wired by a class using
  **`@CrewBase`** and the **`@agent` / `@task` / `@crew`** decorators (the framework auto-collects
  them into `self.agents` / `self.tasks`).
- **Context passing:** a task's **`context=[other_task]`** injects that task's output into this one -
  how outputs chain down the pipeline.
- **Structured output:** **`output_pydantic=Model`** validates a task's result into a Pydantic
  object; **`output_file=`** writes it to disk.
- **Hierarchical process:** add a **`manager_agent`** (with `allow_delegation=True`) and CrewAI lets
  the manager decide task order and delegate - vs. `sequential`, which just runs tasks in order.
- **Extras:** tools like `SerperDevTool` (web search), three memory layers (long-term SQLite,
  short-term RAG, entity), and safe code execution (`allow_code_execution=True`, Docker sandbox).
- Course projects: *debate*, *financial_researcher*, *stock_picker* (hierarchical + manager +
  Pydantic + push), *engineering_team* (lead -> backend -> frontend -> tests), *coder*.

**Built:** a research crew the **idiomatic** way - config-as-data. `config/agents.yaml` +
`config/tasks.yaml` define a Researcher and a Writer; a `@CrewBase` class (`crew.py`) wires them with
`@agent` / `@task` / `@crew` decorators; `main.py` runs `ResearchCrew().crew().kickoff(inputs=...)`.
The Researcher finds 5 key points and the Writer turns them into a briefing - the write task lists
the research task as `context`, so CrewAI hands the research straight through. Writes `briefing.md`.

## Distilled learning

**ELI5:** CrewAI is like hiring a small team. You don't write the steps - you write each teammate's
*job description* (role, goal, backstory) and a list of *tasks*, then say "work through these in
order." Each task can say "you also get the previous task's output" (`context`). The framework runs
the conversation between them for you.

```python
researcher = Agent(role="Senior Researcher", goal="Find 5 key facts about {topic}", backstory="...")
write = Task(description="Write a briefing on {topic}", agent=writer, context=[research])  # chains
crew = Crew(agents=[researcher, writer], tasks=[research, write], process=Process.sequential)
crew.kickoff(inputs={"topic": "agentic AI"})
```
