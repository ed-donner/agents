# Claim Check Team

A multi-agent claim-checking app built with the OpenAI Agents SDK. It searches for current
evidence, tests a factual claim from multiple perspectives, and returns a cited verdict with
calibrated confidence.

## Workflow

1. **Verification Planner** creates five distinct searches.
2. **Evidence Researcher** runs the searches concurrently with OpenAI `WebSearchTool`.
3. **Evidence Analyst** evaluates whether the findings support the claim.
4. **Skeptical Reviewer** looks for contradictions, missing context, and overstatement.
5. **Source Quality Auditor** checks authority, recency, relevance, and independence.
6. **Verdict Editor** weighs the evidence and produces the final cited verdict.

## Requirements

The repository root `.env` must contain:

```text
OPENAI_API_KEY=your-key
```

The optional `DEFAULT_MODEL_NAME` setting controls the model and defaults to
`gpt-5.4-mini`. `CLAIM_CHECK_SEARCHES` controls the number of searches and defaults to `5`.
No third-party search key or external service is required.

## Run

From the repository root:

```powershell
uv run python 2_openai/community_contributions/jualam_claim_check_team/app.py
```

Open the local Gradio URL shown in the terminal, enter a factual claim, and select
**Check claim**.

## Notes

The app prefers primary and recent sources, preserves Markdown citations, and reports
uncertainty when evidence is incomplete or conflicting. Its verdict supports research and
critical thinking; it is not a substitute for professional advice.
