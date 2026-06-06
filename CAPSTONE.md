# Capstone — The Autonomous Research & Action Platform

> The course teaches each skill in isolation. **Mastery is integration.** This
> capstone forces you to combine every framework and every production concern into
> one system you could demo in an interview and defend end-to-end.
>
> If you can build this and explain every design choice, you are not "someone who
> took a course" — you are an AI agent engineer.

---

## Why a capstone (read this first)

Recruiters and senior interviewers don't care that you can call the OpenAI SDK. They care whether you can **make decisions under trade-offs and ship a working system**. A finished capstone gives you:

1. A portfolio artifact with a live demo and a real architecture diagram.
2. Concrete answers to *"tell me about something you built"* — the most common senior question.
3. The integration scars that turn book knowledge into instinct.

Do **not** start this until you've finished Weeks 1–10 and read every `PRIMER.md`. It assumes all of it.

---

## The brief

Build **"Scout"** — an autonomous platform that researches a topic, reasons over what it finds, takes a real action, and runs safely in production.

A user submits a request like:
> *"Research the top 3 competitors to [Company X], summarise their funding and leadership, flag any risks, and email me a report — but ask me before sending."*

Scout must:
1. **Plan** the work and **research** it (multi-agent + web/MCP tools).
2. **Ground** answers in retrieved sources (RAG) and **reason over relationships** (knowledge graph) for questions like "who leads the company that acquired X."
3. **Act** — draft and send an email — but **pause for human approval** before the irreversible send.
4. Run as a **production service** with security, cost controls, observability, and an eval suite that gates changes.

You may scope the domain down (any research topic works), but you may **not** drop any of the four pillars.

---

## Required components (the integration map)

Each pillar must use the real technique from its week. This is the whole point — no shortcuts.

| # | Component | Must use | From |
|---|-----------|----------|------|
| 1 | **Orchestration** | A planner → workers → writer pipeline. Choose ONE framework as the backbone and justify it. | W2 / W3 / W4 |
| 2 | **Tools via MCP** | At least one capability exposed as an **MCP server** (e.g. a "company facts" or "save report" server) and consumed by the agent. | W6 |
| 3 | **Grounded retrieval** | RAG over a source corpus, with **Corrective-RAG** fallback when retrieval is weak. | W7 L1 |
| 4 | **Relational reasoning** | Build a **knowledge graph** from research findings; answer at least one **multi-hop** question from it. | W10 |
| 5 | **Human-in-the-loop** | An **approval gate** on the email send (irreversible action), with a timeout default. | W9 |
| 6 | **Security** | Fail-closed guardrails: prompt-injection detection + PII scrubbing before the LLM. | W7 L5 |
| 7 | **Production service** | FastAPI with health, sessions, rate limiting, and a model fallback chain. | W7 L3 |
| 8 | **Cost & resilience** | Budget middleware (hard-stop) + circuit breaker on the LLM calls. | W7 L10 |
| 9 | **Observability** | Structured logs with correlation IDs + P50/P95/P99 latency + cost tracking. | W7 L4 |
| 10 | **Evaluation + gate** | An eval suite (correctness + consistency + one fairness check) and a CI script that exits non-zero on regression. | W7 L2/L6/L9 |

**Optional stretch (senior+):** containerise and deploy to one cloud (W7 L10 IaC); add a fine-tuned router that sends cheap classification to a small model (W7 L7); add vision (extract facts from a screenshot of a pitch deck — W7 L8); model the orchestration as an explicit LangGraph state machine with a worker/evaluator retry loop (W4).

---

## Architecture you're aiming for

```
                 ┌─────────────────────────────────────────────┐
   user request  │  FastAPI service (health, sessions, limits)  │
   ─────────────▶│                                             │
                 │  Guardrails (injection + PII)  ── fail closed│
                 └───────────────┬─────────────────────────────┘
                                 ▼
        ┌────────────────────────────────────────────────────┐
        │  Orchestrator: Planner → Researchers → Writer       │
        │   │            │              │                      │
        │   │   ┌────────┴───────┐  ┌───┴────┐                 │
        │   │   │ RAG (+CRAG)    │  │ MCP    │  web/company    │
        │   │   │ over corpus    │  │ server │  facts          │
        │   │   └────────┬───────┘  └────────┘                 │
        │   │            ▼                                      │
        │   │   Knowledge Graph (triples) ── multi-hop Q&A      │
        │   ▼                                                   │
        │  Draft email ──▶ [HITL approval gate] ──▶ send (MCP)  │
        └───────────────────────┬───────────────────────────────┘
                                ▼
   middleware: audit → budget → circuit breaker → LLM
   cross-cutting: observability (logs/metrics/traces) + eval suite + CI gate
```

If you can draw this from memory and explain each box's failure mode, you've also passed the hardest [interview](INTERVIEW_BANK.md) question (SD-1/SD-4).

---

## Milestones (suggested 2-week build)

- **Day 1–2:** Orchestration skeleton (planner→worker→writer) on your chosen framework. Hardcode a fake tool. Get an end-to-end "research" run printing a report.
- **Day 3–4:** Add RAG (+CRAG) over a small corpus. Add the MCP server and consume it.
- **Day 5–6:** Build the knowledge graph from findings; answer one multi-hop question.
- **Day 7:** Add the HITL approval gate on the email send (with timeout).
- **Day 8–9:** Wrap in FastAPI; add guardrails (fail closed) and PII scrubbing.
- **Day 10:** Add budget middleware + circuit breaker + observability.
- **Day 11–12:** Write the eval suite + CI gate script. Make a regression fail the build.
- **Day 13:** Stretch goal of your choice.
- **Day 14:** Record a 5-minute demo + write the architecture README. Practice defending every box.

Ship something working on Day 2 and harden it — don't build all pillars half-finished.

---

## Grading rubric (score yourself honestly — 100 pts)

Mastery is not "it runs." It's "it runs, it's defensible, and it fails safely."

### Functionality — 30 pts
- [ ] End-to-end run produces a correct, grounded report (10)
- [ ] Multi-hop question answered from the knowledge graph (8)
- [ ] HITL gate actually pauses the irreversible action and respects approve/reject/timeout (7)
- [ ] MCP server is real (separate process, discovered at runtime) (5)

### Production-readiness — 30 pts
- [ ] Guardrails fail **closed** (prove it: an erroring check blocks) (8)
- [ ] PII never reaches the LLM (prove it: log what the LLM received) (6)
- [ ] Budget hard-stop and circuit breaker both trigger under test (8)
- [ ] Bounded everything: session TTL, capped metrics, loop limits (4)
- [ ] Observability: correlation IDs + latency percentiles + cost (4)

### Evaluation & quality — 20 pts
- [ ] Eval suite covers correctness + consistency + one fairness check (10)
- [ ] CI script exits non-zero on a seeded regression (6)
- [ ] LLM-as-judge biases acknowledged/mitigated in the suite (4)

### Engineering judgement — 20 pts
*(This is the senior section — graded on your README/defense, not just code.)*
- [ ] You justified your framework choice against the alternatives (5)
- [ ] You chose RAG vs KG vs hybrid deliberately and said why (5)
- [ ] Cost is treated as a first-class constraint (model choice, caps, caching) (5)
- [ ] You can name the failure mode of every component (5)

**Scoring:** 90+ = ship it as a portfolio centerpiece. 75–89 = strong, fix the gaps. <75 = revisit the relevant primers; you have knowledge holes the rubric just found.

---

## Defense questions (have answers ready)

A reviewer (or interviewer) will ask:
1. Why this orchestration framework and not the other four?
2. Where exactly does PII get scrubbed, and how do you *know* it never reached the model?
3. What happens if the LLM API goes down mid-request? Mid-research?
4. What happens if the human never responds to the approval gate?
5. How do you know a code change didn't make Scout worse?
6. Where's your biggest cost, and how is it capped?
7. Show me the reasoning path for one knowledge-graph answer.
8. Which single component, if it failed silently, would be worst — and how would you catch it?

If you can answer all eight without hesitation, the [Interview Bank](INTERVIEW_BANK.md) holds no surprises for you.

---

## Done?

Update `MASTERY_CURRICULUM.md`'s final checkbox, record the demo, and write the README as if onboarding a new engineer to Scout. Teaching it back is the final proof you've mastered it.
