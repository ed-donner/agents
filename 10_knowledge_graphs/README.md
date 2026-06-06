# Week 10: Knowledge Graphs

## What you'll build
An agent that reads documents, extracts entities and relationships, builds an in-memory knowledge graph, and answers multi-hop questions by traversing it — without needing a vector DB.

## Learning objectives
- Extract (entity, relation, entity) triples from unstructured text
- Build and query a directed graph with NetworkX
- Answer multi-hop questions: "Who works for the company that acquired X?"
- Persist a graph to/from JSON for reuse across sessions
- Understand when knowledge graphs beat RAG (structured relations vs semantic similarity)

## Labs

| Lab | Topic | Key pattern |
|-----|-------|-------------|
| `1_lab1.ipynb` | Triple extraction | LLM extracts (subject, predicate, object) triples |
| `2_lab2.ipynb` | Graph construction & query | NetworkX graph, BFS/DFS traversal, shortest path |
| `3_lab3.ipynb` | Multi-hop reasoning | Agent answers questions requiring 2-3 graph hops |
| `4_lab4.ipynb` | Graph + RAG hybrid | Knowledge graph for structure, vector search for context |

## App
`app.py` — Paste any text, watch the agent extract a knowledge graph, then ask multi-hop questions about it.

## Dependencies
```
pip install networkx matplotlib
```

## When to use knowledge graphs vs RAG
| Scenario | Use |
|----------|-----|
| "What city is the HQ of the company that acquired X?" | Knowledge graph |
| "What does this document say about pricing?" | RAG |
| "Who are the direct reports of the CEO?" | Knowledge graph |
| "Summarise the main themes of this article" | RAG |
