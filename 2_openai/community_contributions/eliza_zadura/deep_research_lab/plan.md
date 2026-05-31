# Planned Exercise Summary (Week 2)

## Goal

Refactor a single "search + report" agent into a **lightweight, trust-aware agentic workflow** with clear boundaries, minimal cost, and explicit accountability.

---

## Core Design

Focus on *structure over scale*. No agent explosion.

### Workflow Spine

1. **Intake / Framing**

   * Input: topic + constraints
   * Output: 3 follow-up questions + locked research brief

2. **Research Planner**

   * Produces: query clusters, source policy, stop condition

3. **Search Executor (tool)**

   * Executes queries
   * Collects + deduplicates sources/snippets
   * No synthesis

4. **Synthesizer**

   * Builds a **claim ledger** from evidence
   * Notes uncertainty and conflicts

5. **Report Writer**

   * Generates email/report
   * May only use approved claims

(Optional) **QA / Red-team**

* Flags weak claims, missing counterpoints

---

## Two Explicit Improvements to Implement

### A. Source Quality Policy

Treat the internet as adversarial.

Priority ladder:

1. Primary sources (docs, papers, filings)
2. Reputable secondary sources
3. Vendor material (allowed, labeled)
4. Blogs/opinion (framing only)
5. Social media (excluded)

---

### B. Claim Ledger (Trust Mechanism)

Every factual assertion must map to evidence.

Minimal schema:

* **Claim** – single assertion
* **Evidence** – supporting data / quote
* **Source** – where it came from
* **Confidence** – low / medium / high
* **Notes** – caveats, age, bias

Writer cannot invent facts outside the ledger.

---

## Follow-up Questions (Gating Step)

Asked before any searches:

1. Intended outcome / use
2. Scope constraints (time, region, depth, sources)
3. Desired angle (best-case, risks, balanced)

---

## Why This Matters

* Source policy limits **input contamination**
* Claim ledger limits **output overreach**
* Clear handoffs reduce hallucination and token waste
* Enables cheap, practical evaluation ("which claims failed?")

---

## Non-goals

* No benchmark chasing
* No verbose reasoning logs
* No unnecessary agents
