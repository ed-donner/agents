# Week 11: Advanced Evaluation

## What you'll build
A production eval harness that goes beyond LLM-as-judge: adversarial testing, consistency scoring, cost/quality Pareto analysis, and a fairness audit — the kind of eval suite you need before shipping an agent to real users.

## Learning objectives
- Write adversarial prompts that expose agent failure modes
- Measure output consistency: same input → similar output across N runs
- Compute the cost–quality Pareto frontier across models
- Run a basic fairness audit (demographic parity in outputs)
- Build a CI-ready eval suite that blocks deployment on regression

## Labs

| Lab | Topic | Key pattern |
|-----|-------|-------------|
| `1_lab1.ipynb` | Adversarial testing | Prompt injection, jailbreak attempts, edge cases |
| `2_lab2.ipynb` | Consistency & stability | Same input × 10 runs, measure output variance |
| `3_lab3.ipynb` | Cost–quality Pareto | Compare gpt-4o-mini vs gpt-4o vs claude on quality and cost |
| `4_lab4.ipynb` | Fairness audit | Detect demographic bias in agent responses |

## App
`app.py` — Run a full eval suite against any agent function and get an HTML report.

## Cost estimate
~$0.50–2.00 per full eval run (depends on number of test cases and models compared).
