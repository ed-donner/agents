# Week 2 - OpenAI Agents SDK

A lightweight framework that replaces last week's hand-rolled tool loop with real primitives.

- **`Agent(name, instructions, model, tools=, handoffs=, output_type=)`** - a configured LLM.
  Run it with **`Runner.run(agent, message)`** (async) -> `result.final_output`.
- **Tools:** decorate a Python function with **`@function_tool`** and the SDK builds the JSON schema
  from its signature + docstring. Hosted tools too, e.g. **`WebSearchTool(search_context_size=...)`**.
- **Composition, two ways:**
  - **Agents as tools** - `agent.as_tool(tool_name, tool_description)` lets one agent call another
    (orchestrator keeps control).
  - **Handoffs** - `handoffs=[other_agent]` transfers control to another agent.
- **Structured output:** `output_type=MyPydanticModel` guarantees a schema-valid object back
  (great for wiring one agent's output into the next step).
- **Guardrails:** `@input_guardrail` / `@output_guardrail` return `GuardrailFunctionOutput(..., tripwire_triggered=bool)` to block bad input/output.
- **Tracing:** wrap a run in `with trace("name"):` -> full timeline at platform.openai.com/traces.
- **Any model:** `OpenAIChatCompletionsModel(model, openai_client=AsyncOpenAI(base_url=...))` for
  Gemini / DeepSeek / Ollama.
- The course capstone is a **Deep Research** agent: Planner (structured plan) -> parallel Search
  agents (WebSearchTool) -> Writer -> Email (SendGrid).

**Built:** `deep_research.py` - a minimal deep-research agent. A planner returns a structured
`SearchPlan`, the search agents run **in parallel** with `asyncio.gather`, a writer synthesizes one
markdown report, and the whole thing runs inside a single `trace()`. ~50 lines, no email step.

## Distilled learning

**ELI5:** The SDK gives names to last week's hand-built pieces. An `Agent` is the LLM-with-a-job,
`Runner.run` is "go," `@function_tool` turns any Python function into something it can call, and
`output_type` forces it to answer in a fixed shape so the next agent can rely on it. Composing
agents = either let one *use* another as a tool, or *hand off* the conversation entirely.

```python
class SearchPlan(BaseModel):
    searches: list[Search]

planner = Agent("Planner", instructions="...", model="gpt-4o-mini", output_type=SearchPlan)
plan = (await Runner.run(planner, query)).final_output          # guaranteed a SearchPlan
results = await asyncio.gather(*[Runner.run(searcher, s.query) for s in plan.searches])  # parallel
```
