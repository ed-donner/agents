**Project Overview – “LegalDoc Navigator”**

I built a multi‑agent system for a legal‑tech startup that automatically extracts, contextualizes, and answers user queries about complex regulatory documents (e.g., GDPR, HIPAA). The goal was to let non‑experts get precise, actionable answers without sifting through thousands of pages.

---

### 1. Architecture

| Layer | Role | Implementation |
|-------|------|----------------|
| **Data Ingestion** | Parse PDFs, OCR, chunking | LangChain’s `PDFLoader` + custom chunker (max 500 tokens, 50% overlap) |
| **Embedding & Vector Store** | Semantic search | OpenAI `text-embedding-3-large`; Pinecone index (dim 1536) |
| **RAG Agent** | Retrieve relevant snippets | LangGraph `RetrieverNode` + `LLMChain` for re‑ranking |
| **Query‑Planning Agent** | Decompose complex questions | LangChain `ChatPromptTemplate` + Claude‑3.5‑Sonnet (Anthropic) |
| **Action Agents** | Execute sub‑tasks | • **Doc‑Summarizer** (OpenAI GPT‑4o) <br>• **Compliance Checker** (custom rule‑engine) <br>• **Answer Formatter** (OpenAI GPT‑4o) |
| **Orchestration** | Flow control | LangGraph `Graph` with `State` objects, `Condition` nodes for branching |
| **API Layer** | Front‑end integration | FastAPI (Python) → Next.js (React) |
| **Monitoring** | Logging, metrics | OpenTelemetry + Grafana dashboards |

**Workflow Flow**

1. **User Query** → `Query‑Planning Agent` splits into sub‑queries.  
2. Each sub‑query → `RAG Agent` retrieves top‑k snippets.  
3. Snippets + sub‑query → respective `Action Agent`.  
4. Results aggregated by `Answer Formatter`.  
5. Final answer returned to the UI.  

---

### 2. Main Challenges & Solutions

| Challenge | Impact | Solution |
|-----------|--------|----------|
| **Semantic drift between sub‑tasks** | Inconsistent context passed to agents | Implemented a shared `State` object that stores a *cumulative context*; each agent appends its output, and the `Query‑Planning Agent` re‑validates it. |
| **Large documents causing latency** | Retrieval times > 3 s | Switched to Pinecone’s *hybrid* index (vector + metadata filter). Added a *pre‑filter* by document section using a lightweight keyword search, reducing candidate set to 20 chunks. |
| **Agent hallucination** | Wrong legal advice | Added a *Verification Agent* that cross‑checks answers against the original document using a secondary LLM prompt with a higher temperature. Discarded outputs with confidence < 0.7. |
| **Cost control** | High token usage per query | Introduced a *cost‑aware planner* that limits LLM calls to a budget of 200 tokens per sub‑query; fallback to a rule‑based summarizer when over budget. |
| **Deployment latency** | Cold starts on AWS Lambda | Containerized the FastAPI server with Docker, pre‑loaded embeddings, and used AWS Elastic Container Service with a 2‑second warm‑up hook. |

---

### 3. Performance Evaluation

| Metric | Target | Result |
|--------|--------|--------|
| **Average response time** | ≤ 2.5 s | 2.1 s (mean over 1,000 real‑world queries) |
| **Accuracy (legal compliance)** | ≥ 90 % | 92 % (human expert audit on 200 queries) |
| **Cost per query** | ≤ $0.04 | $0.027 (average, including LLM and Pinecone) |
| **User satisfaction** | ≥ 4.5/5 | 4.7/5 (post‑deployment NPS survey) |
| **Throughput** | 50 QPS | 58 QPS (stress test with k6) |

**Evaluation Process**

1. **Unit Tests** – Each agent had deterministic tests with mock embeddings.  
2. **End‑to‑End Tests** – Ran 1,000 synthetic queries covering all sub‑task types.  
3. **Human Review** – Legal experts scored 200 answers for factual correctness and compliance.  
4. **A/B Rollout** – Deployed new pipeline to 20 % of traffic; monitored latency and error rates.  
5. **CI/CD Monitoring** – Automated alerts on latency > 3 s or cost > $0.05 per query.

---

### 4. Takeaways & How It Aligns with the Role

- **Hands‑on LangGraph**: Designed a custom graph with dynamic branching and state sharing—exactly the kind of multi‑agent orchestration you’re looking for.  
- **RAG Mastery**: Built a production‑ready retrieval pipeline with Pinecone, demonstrating deep understanding of embeddings and vector DB tuning.  
- **Python Services**: Delivered a FastAPI backend, fully type‑annotated, Docker‑ready, and integrated with Next.js front‑end.  
- **Startup Agility**: Iterated from MVP to production in 6 weeks, balancing speed with quality—mirroring the “prototype fast, iterate faster” culture.  
- **Anthropic Integration**: Used Claude‑3.5‑Sonnet for planning, showing familiarity with non‑OpenAI LLMs.  
- **Open‑Source Contribution**: Open‑sourced the `LangGraph` helper library we built for dynamic state management; it’s already being used in two other projects.

I’m excited about the opportunity to bring this experience to your team, scaling such pipelines to new domains and driving the next generation of AI‑powered products.