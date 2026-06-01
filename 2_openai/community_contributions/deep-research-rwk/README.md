# Variant of Ed Donner'sdeep_research project
### at https://github.com/ed-donner/agents/tree/main/2_openai/deep_research

## Adds two Agents
- `filter_agent.py`: filters the results of `search_agent.py` by relevance
- `review_agent.py`: evaluates the last draft of the report from `writer_agent.py`
- if the report is not acceptable, the `research_manager` returns the report plus comments to the writer
- after `MAX_REVIEW_ITERATIONS`, the research_manager returns the current draft of the report

## Adds `parameters.py`
- sets various constant parameters for the other modules
- contains all `INSTRUCTIONS` for the Agents
- the sequence of `INSTRUCTIONS` in this file completely describes the workflow

## recasts `plan searches` function
- `plan_searches` calls `search_agent.py`
- `INSTRUCTIONS_SEARCH` directs the agent to conduct the search by:
    - looping over the `WebSearchItem`s in the `WebSearchPlan`, and
    - returning its resulting SearchItems in a SearchResults list