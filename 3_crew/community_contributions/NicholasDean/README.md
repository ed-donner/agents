# Nicholas Dean - Week 3 (CrewAI)

A research crew built the idiomatic CrewAI way - config-as-data.

```
config/agents.yaml   # the Researcher and Writer (role / goal / backstory / llm)
config/tasks.yaml    # research_task and write_task (write_task takes research_task as context)
crew.py              # @CrewBase ResearchCrew, wired with @agent / @task / @crew
main.py              # ResearchCrew().crew().kickoff(inputs={"topic": ...})
```

The Researcher finds 5 key points on a topic and the Writer turns them into a one-page briefing;
because `write_task` lists `research_task` as `context`, CrewAI hands the research straight through.
Writes `briefing.md`.

Run: `uv run --with crewai python main.py "your topic"` (needs `OPENAI_API_KEY`).
