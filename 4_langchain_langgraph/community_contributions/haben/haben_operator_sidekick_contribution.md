# Community Contribution: Sidekick (Operator Agent with LangGraph)

**A high-fidelity autonomous assistant built on LangGraph with a two-LLM (Worker + Evaluator) loop, tool-augmented execution, checkpointed state, and optional browser automation for reliable, human-in-the-loop workflows.**

Repository: [habeneyasu/operator-agent-sidekick](https://github.com/habeneyasu/operator-agent-sidekick)

## Why This Project Stands Out

- **Operator-grade orchestration:** Explicit Worker → Evaluator loop with routing, iteration caps, and structured feedback.
- **Tool-augmented autonomy:** Web search, Wikipedia, Python REPL, filesystem sandbox, and optional Playwright browser.
- **Provider flexibility:** OpenAI-compatible interface with first-class OpenRouter support and model slug configuration.
- **Stateful execution:** Thread-scoped checkpointing enabling safe resume and multi-session reliability.
- **Observability:** LangSmith-ready tracing/metadata and structured logging for production diagnostics.

## System Design at a Glance

`Sidekick` runs a controlled multi-step loop:

1. **Worker LLM (Execution):** Plans and performs steps; invokes tools as needed (search, Python, browser, files).
2. **Evaluator LLM (Quality Gate):** Validates outputs against success criteria and constraints.
3. **Routing:** On failure/insufficiency, returns targeted feedback to the Worker; on success or clarification needed, terminates or pauses.
4. **Safety Controls:** Iteration and token caps; evaluator-triggered user clarification; timeouts for HTTP clients.

This design balances autonomy with reliability, making it suitable for real-world operator workflows that demand traceability and safety.

## Technical Highlights (Industry Best Practice Lens)

| Area | Implementation | Why It Matters |
| --- | --- | --- |
| Orchestration | LangGraph state machine with explicit routes and caps | Predictable control flow and safe retries |
| Agent Roles | Worker (tools) + Evaluator (structured feedback) | Quality gating and reduced error propagation |
| Tools | Search, Wikipedia, Python REPL, files, optional Playwright | Practical autonomy across common ops tasks |
| Provider Abstraction | OpenAI-compatible; OpenRouter via env config | Vendor flexibility and cost/perf agility |
| State & Resume | `thread_id`-scoped checkpointing | Reliability for longer tasks and sessions |
| Observability | LangSmith-compatible tracing and tagging | Production diagnostics and performance insights |

## Key Repository Areas to Explore

- `src/agents/graph.py`: `SidekickGraphState`, `compile_sidekick_graph`, provider routing, loop control.
- `src/agents/worker.py`: History normalization, LLM request assembly, tool execution.
- `src/agents/evaluator.py`: Acceptance criteria, structured feedback parsing, routing flags.
- `src/utils/prompts.py`: Worker and evaluator prompt builders (JSON instruction for evaluator).
- `src/utils/parsing.py`: Converts evaluator text to structured `EvaluatorOutput`.
- `src/tools/`: Tool registry and implementations (search, Wikipedia, Python, Pushover, Playwright, sandbox).
- `src/ui/`: `api.py` helpers and `gradio_app.py` chat UI for interactive runs.
- `src/sidekick.py`: Builders for OpenAI/OpenRouter clients, token caps, and defaults.
- `scripts/run_dev.sh`, `scripts/run_ui.sh`: Dev runner and Gradio launcher (auto-detects OpenRouter).

## Best-Practice Alignment

- **Separation of concerns:** Distinct agent roles, graph orchestration, tool layer, and provider/client builders.
- **Configuration hygiene:** Environment-driven provider selection, model slugs, caps, and optional integrations.
- **Safety-first autonomy:** Evaluator-gated loop with iteration/token limits and explicit user-clarification path.
- **Testability:** Unit suites for state, LLM base, prompts, worker, evaluator, and tools.
- **Operational readiness:** Tracing hooks and structured logging for production diagnostics.

## Evaluation Metrics

To ensure reliability, efficiency, and production readiness, the Sidekick agent is evaluated across five core dimensions:

1. Finality (Evaluator Acceptance Rate)
Definition: Percentage of runs where the evaluator marks `success_criteria_met = true`
Purpose: Measures how often the agent completes tasks successfully without requiring further iterations
Insight: Higher finality indicates stronger reasoning and tool usage
**Observed result: 100.0% acceptance rate** — the evaluator accepted the output on every recorded run.

2. Loop Health (Iterations to Success)
Definition: Number of iterations required to reach a successful outcome (reported as p50 / p95)
Purpose: Evaluates efficiency of the worker–evaluator loop
Insight: Lower values indicate better planning and fewer retries
Note: Track one-shot success rate (success in first iteration) as a key optimization signal
**Observed result: p95 = 0.0 loops** — tasks resolved without requiring additional evaluator-driven retries.

3. Financial Efficiency (Tokens per Run)
Definition: Total tokens consumed per task (worker + evaluator combined)
Purpose: Monitors operational cost of the agent
Insight: Helps optimize prompt design, tool usage, and model selection
Control: Implement kill-switch thresholds to prevent excessive token usage
**Observed result: ~634 tokens avg per run** — lean prompt/completion footprint suitable for cost-sensitive deployments.

4. Reliability (Tool Success Rate)
Definition: Success rate of each tool invocation (per tool basis)
Purpose: Identifies weak or unstable tools in the system
Insight: Enables targeted improvements (e.g., retry logic, better input validation)

5. User Experience (End-to-End Latency)
Definition: Total time taken to complete a task (reported as p50 / p95)
Purpose: Measures responsiveness from the user's perspective
Insight: p95 latency is critical for detecting worst-case delays and bottlenecks
**Observed result: p50 = 111.90s, p95 = 111.90s** — consistent end-to-end latency with no tail-end spikes in the recorded sample.

### Benchmark Summary

| Metric | Value | Notes |
| --- | --- | --- |
| Acceptance Rate | 100.0% | Evaluator finality across all runs |
| Iterations p95 | 0.0 loops | No retries needed to reach success |
| Avg Tokens / Run | ~634 | Combined prompt + completion |
| Latency p50 | 111.90s | Median end-to-end task duration |
| Latency p95 | 111.90s | Tail end-to-end task duration |

![Sidekick benchmark results](Screenshot%20from%202026-03-30%2012-20-50.png)

## Strategic Takeaway

`operator-agent-sidekick` demonstrates how to operationalize multi-step agent workflows without sacrificing safety, clarity, or provider flexibility. Its Worker/Evaluator loop, structured feedback, and tool ecosystem enable practical, auditable autonomy that fits real operator journeys.

## Contact

For collaboration or integration discussions, connect via the repository profile and listed channels.

## Reference

- Project repository: [https://github.com/habeneyasu/operator-agent-sidekick](https://github.com/habeneyasu/operator-agent-sidekick)
