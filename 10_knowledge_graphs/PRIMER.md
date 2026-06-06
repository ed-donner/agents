# Week 10 Primer — Knowledge Graphs for Agentic Reasoning

> Read before the labs. RAG retrieves *passages by similarity*. It cannot reliably
> answer "Who runs the company that acquired the startup our CEO used to work at?"
> — that needs *chained, structured relations*. Knowledge graphs are how agents
> reason over connections, not just over text.

---

## The one mental model

A knowledge graph stores facts as **triples**: `(subject, predicate, object)` — e.g. `(Satya Nadella, CEO_of, Microsoft)`. Many triples form a **graph** where entities are nodes and relations are edges. Now you can *traverse* relationships instead of hoping a single passage contains the whole answer:

```
  RAG (semantic)                 Knowledge Graph (structural)
  query ──embed──▶ nearest       "who runs the co that acquired X?"
  chunks ──▶ LLM                  X ──acquired_by──▶ Co ──CEO──▶ Person
  good for: "what does the        good for: multi-hop relational
  doc say about X?"               questions across many facts

  HYBRID: KG for the relational skeleton + RAG for the prose detail
```

The core skill: **extract structure from unstructured text** (LLM turns prose → triples), build the graph, then answer questions by **multi-hop traversal** (follow edges) rather than single-shot retrieval.

---

## Key concepts, precisely

**Triple extraction (`knowledge_graph.py`, Lab 1).** An LLM with structured output reads text and emits `(subject, predicate, object, confidence)` triples. This is the bridge from messy prose to a queryable structure — and the hardest part to get right (the LLM must be consistent about entity names and predicate vocabulary).

**The graph (NetworkX).** Triples become a directed (multi-)graph. Standard graph ops now apply: `neighbors(entity)`, `shortest_path(a, b)`, degree, connected components.

**Multi-hop queries (Lab 3).** Follow a *chain* of predicates: start entity → relation → intermediate → relation → answer. This is the thing RAG structurally cannot do well: each hop is a precise relational step, not a fuzzy similarity match.

**Question answering.** Two styles: dump relevant triples as context to an LLM (simple), or traverse the graph programmatically then let the LLM phrase the answer (precise). The graph gives you *explainability* — you can show the exact path of facts that produced the answer.

**KG + RAG hybrid (Lab 4).** The strongest pattern. Build both a graph and a vector store from the same corpus. Use the **graph for relational structure** ("who connects to whom") and **RAG for descriptive detail** ("what was said about it"). Ask the LLM to cite which source each fact came from. This combines structural precision with semantic richness — and is exactly how modern "GraphRAG" systems work.

---

## What an interviewer is really testing

- *"When would you use a knowledge graph instead of RAG?"* → For multi-hop relational questions ("who/what connects to what across several facts"), when you need explainable reasoning paths, or when relationships matter more than prose. RAG for "what does this document say"; KG for "how are these entities related." Hybrid when you need both.
- *"What's the hard part of building a KG from text?"* → Reliable triple extraction: entity disambiguation (same entity, different names) and a consistent predicate vocabulary. Garbage/inconsistent extraction makes traversal useless.
- *"Why is a KG more explainable than RAG?"* → The answer is a concrete path of triples you can show; RAG only shows retrieved chunks, not the reasoning chain connecting them.
- *"What is GraphRAG?"* → The hybrid: graph for relational skeleton, vector retrieval for descriptive detail, combined to answer questions neither could alone.

---

## Tradeoffs & gotchas

- **Extraction quality is the ceiling.** Inconsistent entity names ("Microsoft" vs "MSFT" vs "the company") shatter traversal. Normalisation/entity-resolution is essential and underrated.
- **Predicate explosion.** If the LLM invents a new predicate for every sentence, the graph becomes unqueryable. Constrain the relation vocabulary.
- **Graphs go stale.** Facts change (CEOs leave, companies get acquired). A KG needs an update strategy or it confidently returns outdated relations.
- **Not a default.** For most "answer from these docs" tasks, RAG is simpler and sufficient. Use a KG only when relationships and multi-hop reasoning genuinely matter — building/maintaining a graph is real cost.
- **Confidence on triples matters.** LLM-extracted facts can be wrong; carry a confidence and let downstream reasoning weight or filter on it.

---

## Self-test

<details><summary>1. What is a triple and why is it the core unit?</summary>
(subject, predicate, object) — e.g. (Nadella, CEO_of, Microsoft). It's the atomic structured fact; many triples form a traversable graph of entities and relations.</details>

<details><summary>2. What can a KG answer that RAG structurally cannot?</summary>
Multi-hop relational questions — chaining several relations across many facts (e.g. "who runs the company that acquired X?") — by traversing edges rather than matching one passage.</details>

<details><summary>3. What's the hardest part of building a KG from text, and why?</summary>
Reliable triple extraction — entity disambiguation and a consistent predicate vocabulary. Inconsistent names/relations make traversal fail.</details>

<details><summary>4. Describe the KG+RAG hybrid (GraphRAG).</summary>
Build a graph and a vector store from the same corpus; use the graph for relational structure and RAG for descriptive detail, combining both (with source citation) to answer questions neither could alone.</details>

<details><summary>5. When should you NOT reach for a knowledge graph?</summary>
For ordinary "answer from these documents" tasks where relationships don't matter — RAG is simpler, cheaper, and sufficient. A KG adds build/maintenance cost justified only by relational/multi-hop needs.</details>

---

**Labs:** `1` triple extraction → `2` graph queries → `3` multi-hop reasoning → `4` KG+RAG hybrid. App: `app.py` (paste text → see graph → ask multi-hop questions).

**This is the last topic week.** Next: the [Capstone](../CAPSTONE.md) ties every week together, and the [Interview Bank](../INTERVIEW_BANK.md) prepares you to defend all of it.
