# Week 7: Advanced Agentic AI — Closing the 80% → 100% Gap

This folder is a **self-contained supplement** to the Ed Donner course. The course covers the core frameworks and agentic patterns excellently. This week closes the remaining gaps needed for **production-grade** agentic systems.

---

## Why this week exists

The main course leaves eight topics either untouched or only briefly covered:

| Gap | Status in course | Covered here |
|-----|-----------------|--------------|
| Deep RAG pipelines | Mentioned only | Lab 1 |
| Agent evaluation & testing | LLM-as-judge intro only | Lab 2 |
| Agent security & safety | Not covered | Lab 5 |
| Production deployment | HuggingFace Spaces only | Lab 3 |
| Observability & monitoring | LangSmith tracing only | Lab 4 |
| CI/CD eval gate | Not covered | Lab 6 |
| Fine-tuning & distillation | Not covered | Lab 7 |
| Vision & multimodal agents | Single `MultiModalMessage` only | Lab 8 |
| Consistency / cost-quality / fairness evals | Not covered | Lab 9 |
| Enterprise middleware & cloud IaC | Not covered | Lab 10 |

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

### [Lab 6 — CI/CD Eval Gate](6_lab6_cicd_eval_gate.ipynb)
**Wire your eval suite into GitHub Actions so regressions block merges automatically**

- Standalone `run_evals.py` runner — exits with code 1 if avg score < threshold (CI-compatible)
- GitHub Actions workflow (`.github/workflows/eval_gate.yml`) — triggers on every PR, posts a score table as a PR comment, blocks merge on failure
- Pre-push git hook — 3-case smoke eval runs locally before you push (~10s, ~$0.01)
- V1 vs V2 regression comparison with configurable tolerance margin
- Threshold calibration guide: 0.60 for dev iteration → 0.75 for pre-release → 0.80 for production monitoring
- **Connects Lab 2 to the real world**: the eval suite you built now gates every PR automatically

Key packages: `openai`, `pydantic`, GitHub Actions (no extra Python packages needed)

---

### [Lab 7 — Fine-tuning & Knowledge Distillation](7_lab7_finetuning_distillation.ipynb)
**Shrink a large model into a small, cheap, accurate specialist**

- Task selection guide — when fine-tuning beats RAG or prompt engineering (classification/extraction = good; creative/low-volume = bad)
- **Knowledge distillation** — teacher model (gpt-4o) generates labelled examples; student model (gpt-4o-mini) learns the pattern
- JSONL dataset format, train/val split, `client.files.create()` + `client.fine_tuning.jobs.create()`
- Polling for job completion with `client.fine_tuning.jobs.retrieve()`
- Teacher vs student accuracy comparison on held-out test cases
- Cost analysis: gpt-4o vs gpt-4o-mini vs ft:gpt-4o-mini vs gpt-4.1-nano at 10k calls/day
- **`AgentRouter` pattern** — fine-tuned model handles cheap routing decisions; full model handles responses
- Production checklist: dataset drift monitoring, periodic retraining, regression eval before deploying new version

Key packages: `openai`, `pydantic`

---

### [Lab 8 — Vision & Multimodal Agents](8_lab8_vision_multimodal.ipynb)
**Build agents that see — from single images to RAG over image corpora**

- Vision API fundamentals: URL vs base64, `detail` levels (`low`/`high`/`auto`), token cost formula
- **Structured visual extraction** — Pydantic schemas over image content (charts, invoices, documents)
- Multi-image reasoning chains — before/after comparison, image series, cross-document analysis
- Document agent — classify document type, route to the right extraction schema
- **Vision RAG** — index images by LLM-generated descriptions, retrieve by embedding similarity, answer over corpus
- Production patterns: description cache (no repeat API calls), graceful text-only fallback, token cost estimator
- **`MultimodalAgent`** — full agent with mixed text/image conversation history
- Connecting to other labs: vision faithfulness eval (Lab 2), per-session vision token budgets (Lab 3), separate vision token logging (Lab 4), image-embedded prompt injection (Lab 5)

Key packages: `openai`, `pydantic`, `numpy`

---

### [Lab 9 — Advanced Evaluation: Consistency, Cost-Quality & Fairness](9_lab9_advanced_evals.ipynb)
**The eval dimensions beyond correctness — what separates a mid from a senior answer**

- **Consistency** — same input × N runs; measure output stability, and understand why the right target is task-dependent (medical agent → high; brainstorm agent → low)
- Temperature's effect on variance, plus the interview gotcha: temperature 0 is low-variance, *not* deterministic
- **Cost-quality Pareto** — run the same suite across models, pick the cheapest one that clears your bar instead of defaulting to the biggest model
- **Fairness audit** — counterfactual demographic testing: change only a name/age/gender signal, check that answer quality stays equal; flag spreads to investigate
- Builds directly on Lab 2's eval harness (reuse its LLM-as-judge for grading)

Key files: `advanced_evals.py` (`consistency_score`, `pareto_analysis`, `fairness_audit`)

---

### [Lab 10 — Enterprise Deployment: Middleware, Circuit Breakers & Cloud IaC](10_lab10_enterprise_deploy.ipynb)
**Everything an enterprise demands on top of the Lab 3 service**

- **Composable middleware** — `AuditLogger → PIIScrubber → BudgetMiddleware → CircuitBreaker → LLM`, and why the stacking order is deliberate
- **Budget middleware** — per-user and global hard spend caps; the $10 fix for the $10,000 runaway-loop problem
- **Audit logging** — immutable JSONL trail storing prompt *hashes* (never raw PII) for GDPR/HIPAA review, with a right-to-forget pattern
- **Circuit breaker** — CLOSED/OPEN/HALF_OPEN state machine so an upstream LLM outage fails fast instead of exhausting threads and budget
- **Cloud IaC** — the same container on AWS Lambda (Terraform), GCP Cloud Run (YAML), and Azure Container Apps (Bicep), with a decision rule for choosing

Key files: `enterprise_middleware.py`, `circuit_breaker.py`, `deploy/{aws_lambda.tf, gcp_cloudrun.yaml, azure_container_apps.bicep}`

> **Note:** Labs 9 and 10 absorb the former standalone Weeks 11 & 12. Their unique code now lives here as `advanced_evals.py`, `enterprise_middleware.py`, and `circuit_breaker.py`, so Week 7 is the single canonical home for production concerns.

---

## End-to-end architecture

After completing all 8 labs, the pieces fit together like this:

```
User → [Lab 5: Guardrails] → [Lab 3: FastAPI + Sessions]
              ↕                         ↕
       [Lab 1: RAG Pipeline]    [Lab 4: Observability]
       [Lab 8: Vision RAG ]             ↕
              ↕               [Lab 6: CI/CD Gate]
       [Lab 2: Eval Suite] ←→ [Lab 7: Fine-tuned Router]
```

---

## Setup

These notebooks use the same `.env` file and virtual environment as the rest of the course. Install all dependencies with:

```bash
pip install -r requirements.txt
```

Or manually:

```bash
pip install chromadb langchain-chroma langchain-openai langchain-core langgraph fastapi uvicorn pydantic openai numpy
```

All other dependencies (`langchain`, `python-dotenv`) are already in the course environment.

See [requirements.txt](requirements.txt) for pinned versions (tested May 2026).

---

## Recommended order

Security should come **before** deployment — don't ship an agent and then secure it.  
CI/CD comes last — you need evals (Lab 2) before you can gate on them.

```
Lab 1 (RAG) → Lab 2 (Evals) → Lab 9 (Advanced evals) → Lab 5 (Secure it) → Lab 3 (Deploy it safely) → Lab 10 (Enterprise middleware + cloud) → Lab 4 (Monitor it) → Lab 6 (Gate it) → Lab 7 (Fine-tune it) → Lab 8 (Add vision)
```

Labs 7 and 8 are independent of the deployment pipeline — you can do them at any point after Lab 2.  
Lab 9 extends Lab 2 (do it right after). Lab 10 extends Labs 3 and 5 (do it after both).

After completing all 8 labs you'll have the skills to take any agent from the main course and ship it as a production system.
