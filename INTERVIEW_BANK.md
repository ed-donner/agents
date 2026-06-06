# Interview Bank — AI Agent Engineering

> The single document you drill before an interview. It has five parts:
> **(1) Conceptual Q&A**, **(2) System-design prompts**, **(3) Coding drills**,
> **(4) Gotchas & traps**, **(5) Behavioural/decision questions**.
>
> Use it actively: cover the answer, say yours out loud, then compare. Reading it
> is worthless; _retrieving_ it is the point. Each per-week primer
> (`*/PRIMER.md`) has a focused self-test too — this is the cross-cutting layer.

---

## How to use this bank

- **2 weeks out:** one section per day, spoken aloud.
- **3 days out:** all of Part 1 (concepts) + Part 4 (gotchas) in one sitting.
- **Day of:** re-read Part 2 (system design) — that's where senior interviews are won or lost.

A pattern across strong answers: **name the trade-off, then state your default and when you'd deviate.** "X, because Y — but I'd switch to Z when W" beats any one-word answer.

---

# Part 1 — Conceptual Q&A

### Fundamentals (Weeks 1–2)

**Q: What is an agent, precisely?**
An LLM placed in a loop where its output controls which tools are called and when, iterating until a goal is met. The LLM is the controller; tools let it observe and act. Core is a `while not done` loop — frameworks just make it ergonomic.

**Q: When the model "calls a tool," what runs the function?**
Your code. The model only emits a structured request (tool name + args). Your runtime executes the real function and feeds the result back. The model never executes anything.

**Q: How does an LLM have "memory" if it's stateless?**
It doesn't, intrinsically. You resend the conversation (`messages` list) every call. Memory = the list you maintain. Long chats cost more because you pay for the whole history each turn, and eventually hit the context window.

**Q: Handoff vs agent-as-tool (OpenAI SDK)?**
Handoff transfers control to another agent (doesn't return). `as_tool()` calls an agent like a function and returns its result to the caller, which keeps control. Routing → handoff; delegation → as_tool.

**Q: What are structured outputs and why do they matter?**
Forcing the model to return JSON matching a schema (Pydantic). They turn unpredictable text into typed objects your code can branch on — the bridge between "the model said something" and "my program acts on it." Never branch control flow on raw free text.

### Frameworks (Weeks 3–6)

**Q: CrewAI sequential vs hierarchical process?**
Sequential: fixed task order, each output feeds the next — deterministic, debuggable (default). Hierarchical: a manager agent auto-delegates — autonomous but non-deterministic and hard to test. Default sequential; use hierarchical only when decomposition genuinely varies.

**Q: Why model an agent as a LangGraph state machine instead of an SDK?**
Explicit typed state, arbitrary control flow (cycles/branches/retries), per-node testability, and persistence via checkpointing. You trade boilerplate for control. Reach for it when behaviour must be precise and inspectable.

**Q: How does LangGraph give persistent per-user memory?**
Checkpointing (`SqliteSaver`) keyed by `thread_id`. Each thread is an isolated, durable conversation restored on the next call.

**Q: AutoGen AgentChat vs Core — why two layers?**
AgentChat: high-level, rapid prototyping. Core: low-level actor/message-driven runtime for distributed systems. Start high, drop to Core when you need distribution or custom message routing. The gRPC runtime then scales the _same_ agents across machines.

**Q: What problem does MCP solve?**
Tool portability and discovery. Write a tool server once; any MCP-compatible agent can use it, with runtime `list_tools()` discovery and full implementation hiding. "USB-C for AI tools." Cost: a server process + protocol overhead.

**Q: MCP tool vs direct function tool?**
MCP adds portability, dynamic discovery, decoupling — at the cost of running/securing a server. Direct tools are simpler for a single app but lock you to one framework.

### Production (Week 7)

**Q: Your agent works in the demo. What's left before production?**
Walk the pipeline: retrieval accuracy (RAG/CRAG) → an eval suite (correctness + consistency + cost + fairness) wired into a CI gate → security that fails closed → a scalable service (sessions, rate limit, fallback chain) → cost controls + audit + circuit breaker → observability with alerts. Naming these in order is the senior signal.

**Q: What does "fail closed" mean and where does it apply?**
On error, default to the safe/blocking outcome. Applies to security checks: an erroring injection detector must _block_, never pass. (Contrast: a broken metrics collector must NOT take down the request path — that fails open.)

**Q: Name eval dimensions beyond pass/fail correctness.**
Consistency (stability over repeats), cost-quality Pareto (cheapest passing model), fairness (demographic parity), RAG metrics (faithfulness/relevance/hallucination), trajectory (right steps).

**Q: What is Corrective RAG?**
The agent grades its own retrieved context; if it's poor, it rephrases the query and retries before generating — self-correcting retrieval.

**Q: When fine-tune vs RAG vs prompt?**
Prompt for fast iteration; RAG for fresh/large knowledge; fine-tune for high-volume, narrow tasks (classification/extraction) where a distilled small model saves real money at scale. Not for creative/low-volume work.

### Advanced (Weeks 8–10)

**Q: Why do code agents self-improve better than text agents?**
Code is objectively verifiable — run it, get unambiguous pass/fail to feed back. Text has no equivalent ground-truth signal.

**Q: Two signals that decide if an agent step needs a human?**
Confidence below a threshold, and cost/impact above a threshold (or irreversibility). Low-confidence or high-impact → escalate.

**Q: Can you trust an LLM's self-reported confidence?**
No — LLMs are often miscalibrated (confidently wrong). Calibrate thresholds against measured accuracy; where confidence is unreliable, gate on cost/irreversibility instead.

**Q: When KG over RAG?**
Multi-hop relational questions, explainable reasoning paths, relationships > prose. RAG for "what does this doc say"; KG for "how are these entities related." Hybrid (GraphRAG) when you need both.

---

# Part 2 — System-Design Prompts

> Practice these _out loud, end to end_ (~5 min each). Structure every answer:
> **(a) clarify requirements → (b) sketch components → (c) data/control flow →
> (d) failure modes → (e) eval & cost.** That five-beat structure alone reads as senior.

**SD-1. Design a customer-support agent for a SaaS company.**
Expected to cover: RAG over docs/tickets (with CRAG fallback); tools (lookup order, issue refund); **HITL gate on refunds above a threshold**; guardrails (injection, PII scrubbing); session memory; eval suite + CI gate; observability + alerts; budget cap per user; fallback model chain. Bonus: escalation-to-human path and audit logging for compliance.

**SD-2. Design a multi-agent research assistant.**
Planner → parallel search agents (async, I/O-bound) → writer → (optional) email. Structured outputs between stages; trajectory eval (did it search the right things?); cost controls (search calls are expensive); caching. Discuss handoff vs as_tool for the orchestration, and why search runs concurrently.

**SD-3. Design an autonomous code-fixing agent for a CI pipeline.**
Sandbox (subprocess/container, timeout, no network); write→test→fix loop bounded by iterations AND cost; AST validation before running/committing; commit to a branch, never main; HITL or CI gate before merge; held-out tests to prevent overfitting; observability on success rate and cost. Security: treat generated code as hostile.

**SD-4. Design the production deployment for any agent.**
FastAPI (health, SSE, async-safe sessions with TTL, rate limiter, fallback chain) → middleware stack (audit → PII scrub → budget → circuit breaker) → containerised → cloud (Lambda/Cloud Run/Container Apps, with a selection rationale) → observability (structured logs + correlation IDs, P50/95/99 metrics, alerts) → CI eval gate. Emphasise _bounded everything_ and _fail-closed security_.

**SD-5. Design an agent that answers questions over a company's knowledge.**
Decide RAG vs KG vs hybrid: if questions are mostly "what does X say" → RAG; if "how do these relate / multi-hop" → KG; realistically → GraphRAG. Cover ingestion, chunking (8191-token embedding trap), retrieval+rerank, graph extraction quality (entity resolution, predicate vocab), faithfulness eval, and staleness/update strategy.

**SD-6. Design cost & safety controls for an agent serving 100k users.**
Per-user + global budget hard-stops; circuit breaker for upstream outages; rate limiting; cheapest-model-that-passes
(Pareto); response caching; PII scrubbing before the LLM; audit log of hashes (not raw PII); GDPR right-to-forget; fail-closed guardrails; alerting on cost/error/latency windows.

---

# Part 3 — Coding Drills

> Be able to write these from memory. Whiteboard-friendly.

**CD-1. The agent loop from scratch (no framework).**

```python
def run_agent(user_msg, tools, llm):
    messages = [{"role": "system", "content": SYSTEM},
                {"role": "user", "content": user_msg}]
    while True:
        resp = llm(messages, tools=tool_schemas(tools))
        if not resp.tool_calls:
            return resp.content
        messages.append(resp.message)              # keep the tool request
        for call in resp.tool_calls:
            result = tools[call.name](**call.args)  # YOUR code runs it
            messages.append({"role": "tool",
                             "tool_call_id": call.id,
                             "content": str(result)})
```

**CD-2. A safe sandbox runner (subprocess + timeout).**

```python
import subprocess, tempfile, os
def run_code(code, timeout=5):
    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as f:
        f.write(code); path = f.name
    try:
        r = subprocess.run(["python", path], capture_output=True,
                           text=True, timeout=timeout)
        return r.returncode, r.stdout, r.stderr
    except subprocess.TimeoutExpired:
        return -1, "", "TIMEOUT"
    finally:
        os.unlink(path)
```

Talking point: never `exec()` in-process; for real isolation use a container with no network + resource limits.

**CD-3. The write→test→fix loop (bounded).**

```python
def code_agent(problem, tests, llm, max_iter=6, max_cost=0.50):
    code, cost = llm.generate(problem), 0.0
    for _ in range(max_iter):
        ok, output = run_pytest(code, tests)
        if ok: return code
        code, c = llm.fix(problem, code, output)   # feed failure back
        cost += c
        if cost > max_cost: break                   # bound BOTH iter and $
    return None
```

**CD-4. A confidence-gated HITL step.**

```python
def step_with_gate(step, gate, threshold=0.7):
    if step.confidence < threshold or step.cost > COST_LIMIT:
        decision = gate.request(step)              # ask a human
        if decision != "APPROVE":
            return None                            # halt / handle timeout
    return execute(step)
```

**CD-5. Triple extraction signature + traversal.**
Know `(subject, predicate, object, confidence)`, building a `networkx` DiGraph, and a multi-hop query as "follow predicate chain from start node." Be able to sketch `neighbors()` and `shortest_path()` usage.

**CD-6. A circuit breaker (state machine).**
Know the three states (CLOSED/OPEN/HALF_OPEN), the transitions (failure_threshold opens it; recovery_timeout → HALF_OPEN; success_threshold closes it), and that OPEN fails fast / serves a fallback without calling the API.

---

# Part 4 — Gotchas & Traps

These are the questions that catch people who only _used_ agents as a black box.

- **"Does the model run the tool?"** → No. It emits a request; your code runs it.
- **"Is temperature 0 deterministic?"** → No — low-variance, not deterministic (GPU/MoE non-determinism). Say "low variance."
- **"Just gate every action for safety?"** → No — approval fatigue makes humans rubber-stamp. Gate by risk.
- **"Trust the agent's confidence score?"** → No — miscalibration. Calibrate against real accuracy.
- **"Bigger model is better?"** → Pick the cheapest model that passes your eval (Pareto).
- **"Embedding handles long docs?"** → `text-embedding-3-small` silently truncates at 8191 tokens. Chunk first.
- **"Bound the fix loop on iterations?"** → Bound on iterations AND dollars; detect non-improving loops.
- **"Commit the agent's fix to main?"** → Branch, AST-validate, test, then gate/human-merge.
- **"Security check errored — let it through?"** → Fail closed. Always block on error.
- **"Metrics collector errored — fail the request?"** → No, that fails open; don't take down the request path for telemetry.
- **"Memory grows forever — fine?"** → Bound it: session TTL, capped metric deques, history truncation/summarisation.
- **"Log the prompt for compliance?"** → Log a _hash_ + preview, never raw PII. Scrub before the LLM, too.
- **"LLM-as-judge is ground truth?"** → It has length/position/self-preference biases; control for them.

---

# Part 5 — Behavioural / Decision Questions

**Q: How do you decide which agent framework to use?**
Map the need: simple loop → raw API or OpenAI SDK; declarative role-based team → CrewAI; precise control/branching/persistence → LangGraph; distributed/message-driven → AutoGen; portable/reusable tools across frameworks → MCP. Lead with the decision criteria, not a favourite.

**Q: How do you know your agent is good — and stays good?**
Eval suite across correctness/consistency/cost/fairness, wired into a CI gate so regressions can't merge, plus production monitoring with windowed alerts. "Good" is a measured, gated, monitored property — not a one-time check.

**Q: An agent in production starts giving worse answers. How do you debug?**
Read traces (which tools/args/paths) → check eval suite for the regression (and which category) → check observability (latency/error/cost anomalies, model or prompt change) → check retrieval quality if RAG-backed → check for input drift. Localise to a pipeline stage, then fix and add a regression test.

**Q: How do you control agent costs?**
Cheapest-model-that-passes (Pareto), per-user + global budget hard-stops, caching, bounded loops, and cost as a tracked metric with alerts. Treat cost as a first-class engineering constraint, not an afterthought.

**Q: How do you make an autonomous agent safe to deploy?**
Fail-closed guardrails (injection/jailbreak/PII), sandboxing for any code/tool execution, HITL gates on high-impact/irreversible actions, audit logging, circuit breakers, and budget caps. Defense in depth — no single control is trusted alone.

---

## Final check: can you draw the whole system?

If you can sketch — from memory — **user → guardrails → RAG → agent loop → service → middleware → observability → eval/CI gate**, label each box with its failure mode, and state one trade-off per box, you are interview-ready. That diagram _is_ the [Capstone](CAPSTONE.md).
