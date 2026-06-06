# Week 7 Primer — Production-Grade Agentic AI

> Read before the labs. Weeks 1–6 made agents *work*. Week 7 makes them
> *shippable*: retrieval that's accurate, evals you can trust, security that
> fails closed, deployment that scales, observability so you know when it breaks,
> CI gates, fine-tuning, and vision. This is the week that turns a demo into a
> system — and it's where most interview "depth" questions live.

---

## The one mental model

A production agent isn't one model call — it's a **pipeline of defended stages**:

```
 User
   │
   ▼  [Lab 5] Guardrails — injection/jailbreak/PII (fail CLOSED)
   ▼  [Lab 1] RAG — retrieve grounded context (self-correcting)
   ▼  [Lab 8] Vision — if input has images
   ▼  the agent (Weeks 1–6)
   ▼  [Lab 3] FastAPI service — sessions, rate limit, fallback chain
   ▼  [Lab 10] Middleware — budget cap, audit log, circuit breaker
   │
   ├── [Lab 4] Observability — logs, metrics (P50/95/99), traces, alerts
   ├── [Lab 2/9] Evals — correctness + consistency + cost/quality + fairness
   └── [Lab 6] CI/CD gate — evals block regressions before merge
              [Lab 7] Fine-tuning — distil a cheap specialist where it pays
```

Every lab is one defended stage. The senior skill is knowing *which stage a given failure belongs to* — "the agent leaked PII" is a Lab 5 problem; "the bill exploded" is a Lab 10 problem; "quality silently dropped after a deploy" is a Lab 6 problem.

---

## The stages, precisely

**Deep RAG (Lab 1).** Naive RAG = chunk→embed→retrieve→generate. Production RAG adds query expansion, multi-query retrieval, reranking, parent-child chunking, and **Corrective RAG** — the agent *grades its own retrieval* and retries with a rephrased query if results are weak. Key trap: `text-embedding-3-small` silently truncates at 8191 tokens — chunk first.

**Evaluation (Lab 2 + Lab 9).** Lab 2 = the core suite: typed datasets (happy/edge/adversarial/regression), LLM-as-judge with explicit rubrics, RAG metrics (faithfulness, relevance, hallucination), trajectory eval (did it take the right steps?), and regression testing (V1 vs V2). Lab 9 adds the dimensions beyond correctness: **consistency** (same input × N → stable?), **cost-quality Pareto** (cheapest model that passes), **fairness** (counterfactual demographic parity).

**Security (Lab 5).** Prompt injection, jailbreaks, indirect injection, data exfiltration. Two-stage detection (cheap heuristic first, LLM only for ambiguous cases). Tool sandboxing with `realpath()` allowlists (block path traversal). Output filtering (Luhn-validated credit-card redaction, no false positives). **The cardinal rule: security checks fail CLOSED** — if the check errors, *block*, never pass.

**Deployment (Lab 3).** FastAPI with health endpoint, async-safe sessions (`asyncio.Lock`), SSE streaming, TTL session pruning (no unbounded memory), token-bucket rate limiting, model fallback chain (4o → 4o-mini → 3.5) with backoff, response caching, Docker + worker tuning (`2×cores+1`).

**Enterprise middleware & cloud (Lab 10).** Composable wrappers — budget hard-stop, PII scrubber, audit log (hashes, not raw PII), circuit breaker — and the same container on AWS/GCP/Azure via IaC. (Absorbed the former Weeks 11–12.)

**Observability (Lab 4).** Structured JSON logs with correlation IDs, bounded metrics (P50/P95/P99 in a capped deque — no memory leak), async-safe tracing via `ContextVar`, windowed alert rules. You can't operate what you can't see.

**CI/CD eval gate (Lab 6).** `run_evals.py` exits non-zero below threshold; a GitHub Action runs it on every PR and blocks merge on regression. This connects Lab 2 to reality — your eval suite now *guards the repo*.

**Fine-tuning & distillation (Lab 7).** When fine-tuning beats RAG/prompting (high-volume classification/extraction — not creative/low-volume). Teacher (gpt-4o) labels data → student (gpt-4o-mini) learns it → cheap specialist. Plus the `AgentRouter`: cheap fine-tuned model routes, full model answers.

**Vision (Lab 8).** Structured extraction over images (invoices, charts), multi-image reasoning, document routing, and Vision RAG (index images by LLM descriptions, retrieve by embedding).

---

## What an interviewer is really testing

- *"Your agent works in the demo. What's left before production?"* → This *is* Week 7. Walk the pipeline: retrieval accuracy, an eval suite + CI gate, security (fail-closed), a scalable service with fallbacks, cost controls, observability with alerts. Naming all of these, in order, is a senior signal.
- *"How do you know your agent is good — and stays good?"* → Eval suite across correctness/consistency/cost/fairness (Lab 2/9), wired into a CI gate (Lab 6) so regressions can't merge, plus production monitoring/alerts (Lab 4).
- *"Should security run before or after deployment?"* → Before. You don't ship then secure. (Lab order: 5 before 3.)
- *"When fine-tune vs RAG vs prompt?"* → Prompt for quick iteration; RAG for fresh/large knowledge; fine-tune for high-volume narrow tasks where a small specialist saves real money. (Lab 7 task-selection guide.)

---

## Tradeoffs & gotchas

- **Fail closed on safety; fail open elsewhere.** A broken guardrail must block (Lab 5). A broken metrics collector must *not* take down the request path (Lab 4). Knowing which is which is the whole game.
- **Bounded everything.** Sessions (TTL), metrics (capped deque), retries, budgets. Unbounded = a 3am incident.
- **Evals are only useful if they gate.** A suite nobody runs rots. Lab 6 makes it automatic.
- **LLM-as-judge has biases** (length, position, self-preference). Control for them; don't treat judge scores as ground truth.
- **Cost is an engineering metric.** Cheapest-model-that-passes (Lab 9) and budget caps (Lab 10) are senior instincts, not afterthoughts.

---

## Self-test

<details><summary>1. What does "fail closed" mean and where does it apply?</summary>
If a check errors, default to the safe/blocking outcome. Applies to security checks (Lab 5): an erroring injection detector must block, never let the request through.</details>

<details><summary>2. Name the eval dimensions beyond pass/fail correctness.</summary>
Consistency (stability over repeats), cost-quality Pareto (cheapest passing model), fairness (demographic parity), plus RAG metrics (faithfulness/relevance/hallucination) and trajectory (right steps).</details>

<details><summary>3. What is Corrective RAG?</summary>
The agent grades its own retrieved context; if quality is poor it rephrases the query and retries before generating — self-correcting retrieval.</details>

<details><summary>4. Why must metrics/sessions be bounded?</summary>
Unbounded growth (metrics lists, sessions) leaks memory and crashes the service. Use capped deques and TTL pruning.</details>

<details><summary>5. When does fine-tuning beat RAG?</summary>
High-volume, narrow, well-defined tasks (classification/extraction) where a distilled small model is cheaper at scale. Not for creative or low-volume work — use RAG/prompting there.</details>

---

**Labs (recommended order):** 1 RAG → 2 Evals → 9 Advanced evals → 5 Secure → 3 Deploy → 10 Enterprise+cloud → 4 Observe → 6 CI gate → 7 Fine-tune → 8 Vision.

**Next:** [Week 8 Primer](../8_code_agents/PRIMER.md) — agents that write and fix code.
