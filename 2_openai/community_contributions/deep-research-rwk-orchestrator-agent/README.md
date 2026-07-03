# Variant of Ed Donner'sdeep_research project
### at https://github.com/ed-donner/agents/tree/main/2_openai/deep_research

### June 11, 2026

## Includes:
- `query_agent.py`: interactive chat in `deep_research.py` to clarify the query if necessary
- `orchestrator_agent.py`: executes the workflow among the other agents to complete a report
- `filter_agent.py`: filters the results of `search_agent.py` by relevance
- `review_agent.py`: evaluates the last draft of the report from `writer_agent.py`
    - if the report is not acceptable, the `research_manager` returns the report plus comments to the writer
    - after `MAX_REVIEW_ITERATIONS`, the research_manager returns the current draft of the report
- `publish_agent`: saves the report in an HTML file

## `parameters.py`
- contains all the INSTRUCTIONS prompts for the agents
- reading these prompts in order provides a complete description of the workflow
