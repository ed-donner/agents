# Week 7: Advanced Agentic AI — Closing the 80% → 100% Gap

This folder is a **self-contained supplement** to the Ed Donner course. The course covers the core frameworks and agentic patterns excellently. This week closes the remaining gaps needed for **production-grade** agentic systems.

---

## Why this week exists

The main course leaves five topics either untouched or only briefly covered:

| Gap | Status in course | Covered here |
|-----|-----------------|--------------|
| Deep RAG pipelines | Mentioned only | Lab 1 |
| Agent evaluation & testing | LLM-as-judge intro only | Lab 2 |
| Agent security & safety | Not covered | Lab 5 |
| Production deployment | HuggingFace Spaces only | Lab 3 |
| Observability & monitoring | LangSmith tracing only | Lab 4 |

---

## Labs

### [Lab 1 — Deep RAG Pipelines](1_lab1_deep_rag.ipynb)
**From naive retrieval to agentic, self-correcting RAG**

- Naive RAG baseline (chunk → embed → retrieve → generate)
- Query expansion with JSON error handling and graceful fallback
- Multi-query retrieval with deduplication
- LLM-based reranking
- Parent-child chunking — with a side-by-side comparison against naive retrieval so you can see the improvement
- **Corrective RAG (CRAG)** — agent grades its own retrieval and retries with a rephrased query if results are poor; threshold calibration explained
- Embedding token limits: `text-embedding-3-small` silently truncates at 8191 tokens — chunk first

Key packages: `chromadb`, `langchain-chroma`, `langchain-openai`, `langchain-core`, `langgraph`

---

### [Lab 2 — Agent Evaluation & Systematic Testing](2_lab2_agent_evals.ipynb)
**Go beyond ad-hoc testing to a full eval pipeline**

- Building a typed eval dataset (happy path, edge cases, adversarial, regression)
- LLM-as-judge with explicit rubrics, cost estimates printed before every run, and support for multiple acceptable correct answers
- RAG-specific metrics: faithfulness, answer relevance, context quality, hallucination detection
- Agent trajectory evaluation — did the agent take the right steps?
- Trajectory eval integrated into `run_eval_suite` end-to-end (not just a standalone demo)
- Regression testing — automated comparison between agent versions (V1 vs V2)
- Dataset size guidance: 10–20 cases for dev, 50–100 for pre-release gate, 200–500+ for production monitoring

Key packages: `openai`, `pydantic`

---

### [Lab 5 — Agent Security & Safety](5_lab5_security_and_safety.ipynb)
**Protect your agent from prompt injection, jailbreaks, and data leaks**

- Input classification with JSON parse errors defaulting to `risk_score=1.0` (fail closed — never fail open on a security check)
- **Prompt injection detection** with two-stage approach: free heuristic pre-filter first, LLM only for ambiguous cases (reduces cost 60–70%)
- Tool sandboxing with `os.path.realpath()` allowlist — prevents path traversal attacks
- Output filtering: credit card redaction with Luhn algorithm validation (no false positives on SKUs/order IDs), SSN and API key detection
- Alternatives comparison: custom classifier vs OpenAI Moderation API (free, fast) vs LlamaGuard (self-hosted)
- Full `AgentGuardrails` wrapper with blocked-request logging for false positive analysis
- Security checklist for production agents

Key packages: `openai`, `pydantic`, `re`

---

### [Lab 3 — Production Deployment](3_lab3_production_deployment.ipynb)
**From Gradio demo to production-ready service**

- FastAPI wrapper with health endpoint, async-safe session management (`asyncio.Lock`), streaming SSE
- Session TTL with `SESSION_TTL_SECONDS` env var — sessions expire and are pruned automatically (no unbounded memory growth)
- Async concurrent request handling with `asyncio.gather(return_exceptions=True)`
- Async-safe token-bucket rate limiter (`is_allowed_async()` for FastAPI handlers)
- Token budget tracking and per-session cost controls
- Model fallback chain (gpt-4o → gpt-4o-mini → gpt-3.5-turbo) with exponential backoff
- Response caching keyed on last user message (not full history — actually cache-hits on repeat questions)
- Docker + docker-compose with `WEB_CONCURRENCY` env var for worker tuning (`2 × cores + 1`)

Key packages: `fastapi`, `uvicorn`, `asyncio`

---

### [Lab 4 — Observability & Monitoring](4_lab4_observability.ipynb)
**Know when your agent is failing before your users tell you**

- Structured JSON logging with correlation IDs (`request_id`, `session_id`) — production log shipping paths shown (CloudWatch, Loki, Datadog)
- Bounded metrics collection: P50/P95/P99 latency in a `deque(maxlen=10_000)` — no unbounded list growth
- Prometheus migration path shown with `prometheus_client` code (in-memory metrics won't work with Prometheus scraping)
- Async-safe distributed tracer using `ContextVar` (safe to use with Lab 3's `asyncio.gather`)
- Windowed alert rules: error rate, P95 latency, cost per call checked over a rolling 5-minute window
- LangSmith integration with live code pattern (`run_name`, `metadata`, `tags`) and UI navigation guide
- **Lab 3 + Lab 4 integration guide** — instrumented `/chat` handler with logging, metrics, tracing, and cache-hit rate all wired together

Key packages: `openai`, `langchain`, stdlib only for the tracer

---

## End-to-end architecture

After completing all 5 labs, the pieces fit together like this:

```
User → [Lab 5: Guardrails] → [Lab 3: FastAPI + Sessions]
              ↕                         ↕
       [Lab 1: RAG Pipeline]    [Lab 4: Observability]
              ↕                         ↕
       [Lab 2: Eval Suite] ←→ [CI/CD regression gate]
```

---

## Setup

These notebooks use the same `.env` file and virtual environment as the rest of the course. No new setup needed beyond:

```bash
pip install chromadb langchain-chroma langchain-openai langchain-core langgraph fastapi uvicorn
```

All other dependencies (`openai`, `langchain`, `pydantic`) are already in the course environment.

---

## Recommended order

Security should come **before** deployment — don't ship an agent and then secure it.

```
Lab 1 (RAG) → Lab 2 (Evals) → Lab 5 (Secure it) → Lab 3 (Deploy it safely) → Lab 4 (Monitor it)
```

After completing all 5 labs you'll have the skills to take any agent from the main course and ship it as a production system.
