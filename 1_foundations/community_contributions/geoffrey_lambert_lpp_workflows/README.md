# Geoffrey Lambert - LPP Workflow Examples

Practical applications of agentic workflow design patterns for Australian Legal Professional Privilege (LPP) classification.

## The Problem

Privilege review is slow, expensive, and high-stakes. Wrongly disclosing privileged material can waive privilege permanently. This project explores how different AI workflow patterns handle privilege classification, including edge cases like waiver.

## What This Demonstrates

6 notebooks exploring workflow patterns from Ed Donner's Agentic AI course, applied to privilege classification:

| Notebook | Pattern | Description | LLM Calls | Avg Time |
|----------|---------|-------------|-----------|----------|
| 01 | Prompt Chaining | Sequential analysis: parties → lawyer? → advice? → privileged? | 3 | 2.1s |
| 02 | Routing | Route documents to specialist classifiers by type | 2 | 1.3s |
| 03 | Parallelization | Multiple models review same document, flag disagreements | 2 | 7.9s |
| 04 | Orchestrator-Worker | Dynamic breakdown for complex email chains | 3+ | 4.4s |
| 05 | Evaluator-Optimizer | Generate classification, critique, improve | 3 | 4.8s |
| 06 | Comparison | Judge compares all approaches for accuracy and robustness | - | - |

## Approach

Each notebook (01-05) demonstrates a single workflow pattern using test emails. This keeps the focus on understanding how each pattern works.

Notebook 06 brings it all together - running a set of test documents through all patterns to compare accuracy, speed, and robustness.

## Australian Law Focus

Applies Evidence Act 1995 (Cth) ss 118-119 and the dominant purpose test from key cases:

- *Esso Australia Resources Ltd v Commissioner of Taxation* (1999) - dominant purpose test
- *AWB Ltd v Cole* (2006) - in-house counsel
- *Mann v Carnell* (1999) - waiver

## Key Findings

### Accuracy Results (from Notebook 06)

| Pattern | Accuracy | Caught Waiver Edge Case? |
|---------|----------|--------------------------|
| **Evaluator-Optimizer** | **3/3 (100%)** | ✓ Yes |
| Prompt Chaining | 2/3 (67%) | ✗ No |
| Routing | 2/3 (67%) | ✗ No |
| Orchestrator-Worker | 1/3 (33%) | ✗ No |
| Parallelization | 1/3 (33%) | ✓ Yes (flagged uncertain) |

### Critical Insight

Only the Evaluator-Optimizer pattern correctly identified that forwarding legal advice to the opposing party created a waiver risk. Self-critique catches what single-pass analysis misses.

## Recommended Hybrid Workflow
```
Incoming Documents
        ↓
   [ROUTING] ← Fast first-pass (1.3s, 2 calls)
        ↓
   ┌────┴────┐
   ↓         ↓
CLEAR     UNCERTAIN
   ↓         ↓
 Done    [EVALUATOR] ← Self-critique (4.8s, 3 calls)
             ↓
        ┌────┴────┐
        ↓         ↓
    RESOLVED   STILL UNCERTAIN
        ↓         ↓
      Done    HUMAN REVIEW
```

## Output

Each notebook exports a CSV for senior lawyer review (HITL) with:
- Classification and confidence score
- Dominant purpose analysis
- Waiver risk assessment
- Escalation flags for uncertain cases
- Blank columns for reviewer notes and final decision

## Setup

### Prerequisites

1. Python 3.10+
2. OpenAI API key in `.env` file
3. Ollama installed with Llama 3.2 (for Notebook 03)

### Install Ollama (for Parallelization)
```bash
# Download from https://ollama.ai
ollama pull llama3.2:1b
```

### Run Notebooks
```bash
cd notebooks
jupyter lab
```

Run notebooks in order (01-06) to see each pattern build on concepts.

## Folder Structure
```
geoffrey_lambert_lpp_workflows/
├── README.md
├── notebooks/
│   ├── 01_prompt_chaining.ipynb
│   ├── 02_routing.ipynb
│   ├── 03_parallelization.ipynb
│   ├── 04_orchestrator_worker.ipynb
│   ├── 05_evaluator_optimizer.ipynb
│   └── 06_evaluation_comparison.ipynb
├── assets/
│   └── (CSV outputs saved here)
└── notebooks/
    └── (working notebooks)
```

## Lessons Learned

1. **No single pattern is best for everything** - match pattern to use case
2. **Edge cases need self-critique** - simple patterns miss subtle waiver issues
3. **Speed vs accuracy trade-off** - Routing is 4x faster but misses nuance
4. **Waiver is hard to catch** - forwarding to third parties needs explicit checking
5. **Hybrid approaches win** - combine patterns for production use


---

## Notebook 07: Agent Loop Analyst

This notebook demonstrates the **agent loop pattern** — identical to Ed Donner's todo example but applied to real-world governance analysis with legal-grade provenance tracking.

### What It Does

1. **Extracts** text and tables from ASX annual report PDFs (AMP 2018 & 2019)
2. **Embeds** 1,562 content chunks into a ChromaDB vector store
3. **Searches** using natural language queries with year/type filtering
4. **Analyses** complex governance questions autonomously
5. **Cites** sources with page-level precision
6. **Verifies** every claim against source documents

### The Agent Loop Pattern

The core insight: **the loop pattern is domain-agnostic**.

| Todo Example | Annual Report Analyst |
|--------------|----------------------|
| `todos = []` | `findings = []` |
| `create_todos()` | `search_report()` |
| `mark_complete()` | `add_finding()` |
| Solves maths problems | Analyses governance questions |

Same `handle_tool_calls()`, same `loop()` — only the tools change.

### Why Provenance Matters

For legal, forensic, and governance work, every claim must be traceable:
```
Agent Claim: "CEO fixed remuneration was $2,200,000"
     ↓
Citation: "2018 Annual Report, Page 42"
     ↓
Vector Store: Content verified at that location
     ↓
Source: AMP_18AR.pdf (manually verifiable)
```

### Results

| Metric | Result |
|--------|--------|
| Text chunks extracted | 1,235 |
| Tables extracted | 327 |
| Total chunks indexed | 1,562 |
| Citations verified | 4/4 traceable to source |
| Data isolation | Confirmed — agent used ONLY loaded PDFs |

### Sample Provenance Verification
```
================================================================================
                         VERIFICATION SUMMARY
================================================================================

  Total Citations:    4
  ✓ Verified:         1
  ~ Partial:          3
  ✗ Not Found:        0

  ALL CITATIONS TRACEABLE TO SOURCE DOCUMENTS
================================================================================
```

### Additional Dependencies
```bash
pip install pymupdf chromadb sentence-transformers
```

### Key Lessons

- **The agent loop is domain-agnostic** — same pattern works for todos, research, analysis
- **Tables matter** — structured data extraction preserves relationships LLMs need
- **Provenance is essential** — for legal work, every claim must be traceable
- **Citation enforcement works** — mandatory page citations prevent hallucination
- **Verification builds trust** — audit trails prove analysis is grounded in source documents

## Author

Geoffrey Lambert - Lawyer & Computer Forensic Specialist | Oxford AI Studies

## Acknowledgements

Based on Ed Donner's [Agentic AI Engineering Course](https://github.com/ed-donner/agents).