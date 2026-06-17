# Mastery Curriculum — From Software Engineer to AI Agent Engineer

> **This is the spine. Start here.** It turns a strong general software engineer
> (new to AI) into someone who can build, ship, and *defend* production agentic
> systems — and pass a senior AI-engineering interview.
>
> The labs alone teach you to type the code. This curriculum adds the three things
> that actually create mastery: **mental models first**, **deliberate interview
> practice**, and **an integration capstone**. Follow the loop for every week and
> you will understand, retain, and be able to explain everything.

---

## Who this is for

A mid-to-senior software engineer fluent in Python and systems, but new to LLMs and agents. AI/LLM concepts are explained from first principles; general engineering (async, APIs, Docker, CI) is assumed.

By the end you can:
- **Build** any agent pattern, from a raw API loop to a distributed multi-agent system.
- **Choose** the right framework/technique for a problem and justify it under trade-offs.
- **Ship** it: secured, evaluated, observable, cost-controlled, deployed.
- **Defend** every design decision in an interview.

---

## The weekly mastery loop (do this every week)

Reading a notebook once teaches almost nothing durable. For **each** week, run this loop:

```
 1. PRIME   → read  <week>/PRIMER.md   (the mental model, ~15 min, BEFORE code)
 2. BUILD   → do the labs in order      (hands on keyboard)
 3. RECALL  → answer the primer self-test from memory (cover the answers)
 4. DEFEND  → answer that week's questions in INTERVIEW_BANK.md, out loud
 5. CONNECT → write one sentence: how does this week build on the last?
```

Steps 1, 3, 4, 5 are what the labs lack and what mastery requires. **Do not skip the primer.** Do not skip saying answers *out loud* — retrieval, not recognition, is what sticks.

---

## The 10-week sequence

| Wk | Topic | Mental model | Primer | Build |
|----|-------|--------------|--------|-------|
| 1 | **Foundations** | LLM = stateless function; agent = the loop | [primer](1_foundations/PRIMER.md) | [labs](1_foundations/) |
| 2 | **OpenAI Agents SDK** | The loop, wrapped; compose agents | [primer](2_openai/PRIMER.md) | [labs](2_openai/) |
| 3 | **CrewAI** | Declarative role-based teams (org chart) | [primer](3_crew/PRIMER.md) | [projects](3_crew/) |
| 4 | **LangGraph** | Agent as explicit typed state machine | [primer](4_langgraph/PRIMER.md) | [labs](4_langgraph/) |
| 5 | **AutoGen** | Actor model; message-driven → distributed | [primer](5_autogen/PRIMER.md) | [labs](5_autogen/) |
| 6 | **MCP** | Standard protocol; tools decoupled from frameworks | [primer](6_mcp/PRIMER.md) | [labs](6_mcp/) |
| 7 | **Production** | A pipeline of defended stages | [primer](7_advanced/PRIMER.md) | [10 labs](7_advanced/) |
| 8 | **Code Agents** | The loop + tests as the verifier | [primer](8_code_agents/PRIMER.md) | [labs](8_code_agents/) |
| 9 | **Human-in-the-Loop** | Risk-based selective approval gates | [primer](9_human_in_the_loop/PRIMER.md) | [labs](9_human_in_the_loop/) |
| 10 | **Knowledge Graphs** | Triples + multi-hop traversal (vs RAG) | [primer](10_knowledge_graphs/PRIMER.md) | [labs](10_knowledge_graphs/) |
| ★ | **Capstone** | Integrate *everything* into one system | — | [CAPSTONE.md](CAPSTONE.md) |

> **History note:** Weeks 11 and 12 (standalone Advanced-Eval and Enterprise-Deploy)
> were merged into Week 7 as **Lab 9** (consistency/Pareto/fairness) and **Lab 10**
> (middleware/circuit-breaker/cloud IaC), so every production topic has one
> canonical home. There is no separate Week 11/12 anymore.

---

## The conceptual spine (how the weeks connect)

Each week is a deliberate step. Internalise *why this order*:

```
 W1  the agent loop, by hand ........... the irreducible core
  │
 W2  loop wrapped by an SDK ............ ergonomics + composition
 W3  declarative teams ................. abstraction up (YAML)
 W4  explicit state machines ........... abstraction down (control)
 W5  message-driven / distributed ...... scale out (actors)
 W6  MCP ............................... decouple tools from all of the above
  │
 W7  PRODUCTION ........................ make any of it shippable
  │   (RAG, evals, security, deploy, observe, CI, fine-tune, vision,
  │    + advanced evals + enterprise middleware + cloud)
  │
 W8  code agents ...................... the loop + an objective verifier
 W9  human-in-the-loop ................ keep humans in control of autonomy
 W10 knowledge graphs ................. structured reasoning beyond RAG
  │
 ★  CAPSTONE .......................... prove integration
```

Weeks 2–6 are five *lenses* on the same agent loop — learn to pick the right lens. Week 7 is the load-bearing production week. Weeks 8–10 are advanced capabilities. The capstone forces them together.

---

## Recommended pacing

**Full (10–12 weeks, ~8–10 h/week)** — one topic week per calendar week, capstone over the final 2. Best retention.

**Intensive (5–6 weeks, ~20 h/week)** — two topic weeks per week; Week 7 gets its own full week (it's 10 labs); capstone last. For full-time study.

**Interview crunch (2 weeks)** — you already know the material and need to be sharp: Day 1–3 read all 10 primers; Day 4–7 all of `INTERVIEW_BANK.md` out loud; Day 8–14 build a *scoped* capstone for a portfolio artifact. Don't attempt this without prior exposure.

Within Week 7, the lab order is: **1 RAG → 2 Evals → 9 Advanced evals → 5 Secure → 3 Deploy → 10 Enterprise+cloud → 4 Observe → 6 CI gate → 7 Fine-tune → 8 Vision.** (Security before deployment; evals before the CI gate.)

---

## Mastery checkpoints

Don't advance past a checkpoint until you can do it **from memory, out loud**:

- [ ] **After W1:** Write the agent loop on a whiteboard. Explain why the model doesn't run tools.
- [ ] **After W6:** Given a problem, pick a framework (or MCP) and defend it against the other options.
- [ ] **After W7:** List, in order, everything between a demo agent and a production one — with each component's failure mode.
- [ ] **After W10:** Decide RAG vs KG vs hybrid for a scenario and justify it.
- [ ] **After Capstone:** Score ≥75 on the rubric and answer all 8 defense questions without hesitation.
- [ ] **Interview-ready:** Draw `user → guardrails → RAG → agent → service → middleware → observability → eval/CI gate` from memory, labelling each box's failure mode and one trade-off.

---

## What "100%" / mastery looks like

You have mastered this track when you can, *without notes*:

1. **Explain** the agent loop from first principles and why frameworks exist.
2. **Choose** among OpenAI SDK / CrewAI / LangGraph / AutoGen / MCP for a given problem and defend it.
3. **Build** RAG (with self-correction), code agents, HITL gates, and knowledge graphs.
4. **Productionise** anything: fail-closed security, evals + CI gate, scalable service, cost caps, observability, cloud deploy.
5. **Defend** every decision against its trade-offs and name every component's failure mode.
6. **Ship** the capstone and teach it back to another engineer.

That last point is the real test. *If you can teach it, you own it.*

---

## Map of everything in this track

```
agents/
├── MASTERY_CURRICULUM.md     ← you are here (the spine)
├── INTERVIEW_BANK.md         ← concepts, system design, drills, gotchas
├── CAPSTONE.md               ← the integration project + rubric
│
├── 1_foundations/  … 10_knowledge_graphs/
│   ├── PRIMER.md             ← read FIRST each week (mental model)
│   ├── README.md             ← lab index (Ed Donner + additions)
│   └── *.ipynb / *.py        ← the labs and modules
│
└── 7_advanced/               ← the production week (10 labs)
    ├── 9_lab9_advanced_evals.ipynb     (consistency/Pareto/fairness — ex-W11)
    ├── 10_lab10_enterprise_deploy.ipynb (middleware/circuit-breaker/cloud — ex-W12)
    ├── advanced_evals.py, enterprise_middleware.py, circuit_breaker.py
    └── deploy/ (aws_lambda.tf, gcp_cloudrun.yaml, azure_container_apps.bicep)
```

Begin with [Week 1's primer](1_foundations/PRIMER.md). Read it before you open a single notebook.
