# Advanced Track — Weeks 8–12

These five weeks extend the original course from 80% to 100% production-readiness.  
They pick up directly after Week 7 (Advanced Topics).

---

## Who these weeks are for

You've finished Weeks 1–7. You can build and deploy a working agent.  
Now you need to build one that's **safe, testable, maintainable, and enterprise-deployable**.

---

## Overview

| Week | Topic | Core skill you gain |
|------|-------|---------------------|
| **8** | [Code Agents](8_code_agents/) | Agents that write, run, and fix code in a loop |
| **9** | [Human-in-the-Loop](9_human_in_the_loop/) | Approval gates, confidence escalation, feedback |
| **10** | [Knowledge Graphs](10_knowledge_graphs/) | Structured multi-hop reasoning without a vector DB |
| **11** | [Advanced Evaluation](11_advanced_eval/) | Adversarial testing, consistency, cost-quality Pareto |
| **12** | [Enterprise Deployment](12_enterprise_deploy/) | Docker, AWS/GCP/Azure, PII scrubbing, audit logs |

---

## Week 8 — Code Agents

**The gap it fills:** The course shows CrewAI's coder agent as a demo. Week 8 teaches the actual mechanism: write → sandbox → test → fix → loop.

**What you build:**
- `sandbox.py` — subprocess-isolated Python executor with timeout
- `code_agent.py` — write→pytest→fix loop with cost tracking
- `git_agent.py` — read repo, AST-analyse, fix, commit to branch
- `app.py` — Gradio UI: paste a failing test, watch it pass

**Key files:**
```
8_code_agents/
├── sandbox.py        ← safe subprocess executor
├── code_agent.py     ← the write→test→fix loop
├── git_agent.py      ← Git-integrated version
├── app.py            ← Gradio UI
├── 1_lab1.ipynb      ← sandbox execution
├── 2_lab2.ipynb      ← test-driven fix loop
├── 3_lab3.ipynb      ← AST-aware editing
└── 4_lab4.ipynb      ← Git integration
```

---

## Week 9 — Human-in-the-Loop

**The gap it fills:** Every enterprise AI product needs approval gates. Without them, a bug sends 10,000 emails or executes large trades before anyone notices.

**What you build:**
- `hitl.py` — `ApprovalGate`, `HITLAgent`, `FeedbackStore`
- `app.py` — Gradio UI with real-time step-by-step approval
- 4 labs: gates, confidence scoring, feedback propagation, multi-agent arbitration

**Key patterns:**
- Auto-approve below confidence/cost thresholds
- Callback-based gates (wires into Gradio, Slack, email)
- Feedback accumulated across steps in a session
- Human resolves disagreement between 2+ agents

```
9_human_in_the_loop/
├── hitl.py           ← core HITL framework
├── app.py            ← Gradio approval UI
├── 1_lab1.ipynb      ← approval gates
├── 2_lab2.ipynb      ← confidence + escalation
├── 3_lab3.ipynb      ← feedback loops
└── 4_lab4.ipynb      ← multi-agent arbitration
```

---

## Week 10 — Knowledge Graphs

**The gap it fills:** RAG can't answer "Who runs the company that acquired X?" — that requires chaining structured relations. Knowledge graphs can.

**What you build:**
- `knowledge_graph.py` — LLM triple extraction + NetworkX graph + Q&A
- `app.py` — paste text → see graph → ask multi-hop questions
- 4 labs: extraction, traversal, multi-hop, KG+RAG hybrid

**When to use KG vs RAG:**
- KG: structured relations ("who works for who", "what owns what")
- RAG: semantic context ("what does this document say about X")
- Hybrid: "What did the CEO of the company that acquired X say about Y?"

```
10_knowledge_graphs/
├── knowledge_graph.py   ← extractor + graph + Q&A engine
├── app.py               ← Gradio explorer
├── 1_lab1.ipynb         ← triple extraction
├── 2_lab2.ipynb         ← graph queries
├── 3_lab3.ipynb         ← multi-hop reasoning
└── 4_lab4.ipynb         ← KG + RAG hybrid
```

---

## Week 11 — Advanced Evaluation

**The gap it fills:** Week 7 covers LLM-as-judge and basic evals. Week 11 adds adversarial testing, consistency measurement, cost-quality Pareto, and fairness auditing — the evals you need before shipping to real users.

**What you build:**
- `eval_harness.py` — `AgentEvaluator`, `EvalReport`, `consistency_score`, `pareto_analysis`
- 4 labs: adversarial, consistency, Pareto, fairness

**What each lab teaches:**
1. **Adversarial** — prompt injection, jailbreaks, indirect injection, data extraction
2. **Consistency** — same question × 10 runs, measure output variance at different temperatures
3. **Pareto** — compare models on cost vs quality, find the cheapest model that meets your bar
4. **Fairness** — counterfactual testing, demographic parity, differential refusal rates

```
11_advanced_eval/
├── eval_harness.py    ← eval framework
├── 1_lab1.ipynb       ← adversarial testing
├── 2_lab2.ipynb       ← consistency scoring
├── 3_lab3.ipynb       ← cost-quality Pareto
└── 4_lab4.ipynb       ← fairness audit
```

---

## Week 12 — Enterprise Deployment

**The gap it fills:** The course deploys to HuggingFace Spaces. Enterprises deploy to AWS, GCP, or Azure — with PII controls, audit trails, cost limits, and circuit breakers.

**What you build:**
- `middleware.py` — `BudgetMiddleware`, `PIIScrubber`, `AuditLogger`
- `circuit_breaker.py` — fail-fast pattern for LLM API outages
- `agent_server.py` — production FastAPI server with all middleware stacked
- `Dockerfile` — multi-stage production container
- `deploy/aws_lambda.tf` — Terraform for AWS Lambda + API Gateway
- `deploy/gcp_cloudrun.yaml` — GCP Cloud Run deployment
- `deploy/azure_container_apps.bicep` — Azure Container Apps

**The production middleware stack:**
```
Request
  → AuditLogger      (immutable compliance log)
  → PIIScrubber      (GDPR: no PII reaches the LLM)
  → BudgetMiddleware (hard-stop at spending limit)
  → CircuitBreaker   (fail fast if API is down)
  → LLM
```

```
12_enterprise_deploy/
├── middleware.py             ← budget + PII + audit stack
├── circuit_breaker.py        ← fault tolerance
├── agent_server.py           ← FastAPI server
├── Dockerfile                ← multi-stage production build
├── requirements.txt
├── deploy/
│   ├── aws_lambda.tf         ← Terraform: Lambda + API Gateway
│   ├── gcp_cloudrun.yaml     ← Cloud Run YAML
│   └── azure_container_apps.bicep
├── 1_lab1.ipynb              ← Docker + FastAPI
├── 2_lab2.ipynb              ← cost controls
├── 3_lab3.ipynb              ← PII + audit log
└── 4_lab4.ipynb              ← cloud IaC + circuit breaker
```

---

## Recommended learning order

1. **Week 8** (Code Agents) — independent, good starting point
2. **Week 9** (HITL) — independent, good starting point
3. **Week 10** (Knowledge Graphs) — independent
4. **Week 11** (Eval) — do this before Week 12 (test before you deploy)
5. **Week 12** (Deploy) — do this last; it wraps everything

Weeks 8 and 9 can be done in parallel. Week 12 builds on all previous weeks.

---

## Setup

All weeks use the same base environment as Weeks 1–7.  
Additional packages per week are listed in each `README.md`.

```bash
# Week 8 extras
pip install gitpython pytest

# Week 10 extras
pip install networkx matplotlib

# Week 12 extras
pip install fastapi uvicorn[standard]
```

---

## Cost estimates

| Week | Typical cost per session |
|------|--------------------------|
| 8    | $0.05–0.20              |
| 9    | $0.02–0.10              |
| 10   | $0.05–0.15              |
| 11   | $0.50–2.00              |
| 12   | $0.01–0.05              |

All labs are designed to use `gpt-4o-mini` by default to keep costs low.

---

## What 100% looks like

After completing Weeks 1–12 you can:

- **Build** — any agent pattern from raw API to multi-agent graph
- **Test** — adversarial + consistency + fairness + cost benchmarks
- **Secure** — HITL approval gates, PII scrubbing, prompt injection defense
- **Reason** — structured knowledge graphs for multi-hop questions
- **Deploy** — Docker container to AWS, GCP, or Azure with cost controls
- **Operate** — audit logs, circuit breakers, budget alerts, GDPR compliance
