# Week 9 Primer — Human-in-the-Loop (HITL)

> Read before the labs. Full autonomy is a liability for high-stakes actions. Every
> serious enterprise AI product has approval gates — without them, a single bug
> sends 10,000 emails or executes a bad trade before anyone notices. This week is
> about putting a human in control *without* destroying the agent's usefulness.

---

## The one mental model

HITL inserts **decision gates** into the agent's execution. The art is **not** gating everything (that defeats automation) — it's gating *selectively* based on **risk**, so humans review only what matters:

```
   agent proposes a step
            │
            ▼
   ┌──────────────────┐    low risk      ┌──────────┐
   │  needs_human()?  │─────────────────▶│ auto-run │
   │  confidence<thr  │                  └──────────┘
   │   OR cost>thr    │    high risk
   └────────┬─────────┘─────────┐
            │                   ▼
            │            ┌───────────────┐  APPROVE → run
            │            │ human reviews │  REJECT  → halt
            │            └───────────────┘  feedback → influences next step
            ▼
        proceed / halt
```

The gate is driven by **confidence** (the agent's own self-assessed certainty) and **cost/impact** (dollars, irreversibility). Low-confidence or high-impact → escalate to a human; everything else flows automatically.

---

## Key concepts, precisely

**The approval gate (`hitl.py`).** A `Step` carries a `payload`, a `confidence`, a `cost_estimate`, and a `requires_approval` flag. `needs_human(step)` returns true when confidence < threshold OR cost > threshold. The `ApprovalGate` supports pluggable backends: `cli` (terminal prompt), `auto` (always approve — for tests), and `callback` (calls your function — this is how it wires into Gradio, Slack, or email).

**Confidence scoring (Lab 2).** Force the agent to emit a structured `confidence` (0–1) via Pydantic alongside its answer, then **route on it**: high → auto, low → human. Crucial caveat: **LLMs are often poorly calibrated** — they can be confidently wrong. So you *calibrate*: check predicted confidence against known-answer accuracy, and set thresholds from real data, not vibes.

**Feedback propagation (Lab 3).** A `FeedbackStore` accumulates human corrections across a session and injects them as context into later steps (`as_context()`). The human's correction on step 2 improves step 5. This is how HITL gets *cheaper over time* — the agent learns the operator's preferences within the session.

**Callback architecture (`app.py`).** The agent runs on a background thread; the gate blocks on a queue waiting for the UI's response. This async hand-off (agent thread ↔ UI thread via queues) is the real engineering pattern behind any "agent paused, waiting for your approval" UX.

**Multi-agent arbitration (Lab 4).** When two agents disagree, a human resolves the tie. HITL as conflict resolution, not just approval.

---

## What an interviewer is really testing

- *"How do you add human oversight without killing throughput?"* → Risk-based selective gating: auto-approve low-confidence/low-impact, escalate only high-risk steps. Drive it with calibrated confidence + cost/impact thresholds. The naive answer ("approve everything") shows you've never operated one.
- *"Can you trust an LLM's confidence score?"* → Not blindly — LLMs are frequently miscalibrated (confidently wrong). You must calibrate thresholds against measured accuracy and treat self-reported confidence as a noisy signal, not truth.
- *"How does human feedback improve the agent during a session?"* → Accumulate corrections in a store and inject them as context into subsequent steps, so earlier corrections shape later behaviour.
- *"How do you implement 'agent waits for approval' technically?"* → Run the agent off the request thread; the gate blocks on a queue/event until the human responds (callback backend). Don't block the UI.

---

## Tradeoffs & gotchas

- **Approval fatigue.** Gate too much and humans rubber-stamp everything — worse than no gate (false sense of safety). Tune thresholds so humans see *only* genuinely risky items.
- **Confidence ≠ correctness.** Miscalibration means a 0.9 confidence isn't 90% accuracy. Calibrate, and prefer cost/irreversibility as a gate where confidence is unreliable.
- **Timeouts need a default.** What happens if the human never responds? Define it (halt vs auto-reject) — `Decision.TIMEOUT` exists for this. A hung gate is a hung product.
- **Latency cost.** A human in the loop adds minutes. Reserve it for steps where the risk justifies the wait; everything else stays autonomous.
- **Audit the decisions.** Who approved what, when? HITL decisions are compliance-relevant (ties to Week 7 audit logging).

---

## Self-test

<details><summary>1. What two signals decide whether a step needs a human?</summary>
Confidence (below a threshold) and cost/impact (above a threshold, or irreversible). Low-confidence or high-impact → escalate.</details>

<details><summary>2. Why can't you trust an LLM's self-reported confidence directly?</summary>
LLMs are often miscalibrated — confidently wrong. You must calibrate thresholds against measured accuracy and treat confidence as a noisy signal.</details>

<details><summary>3. How does human feedback help later steps in the same session?</summary>
A FeedbackStore accumulates corrections and injects them as context into subsequent steps, so an early correction shapes later agent behaviour.</details>

<details><summary>4. What is approval fatigue and how do you avoid it?</summary>
When over-gating makes humans rubber-stamp everything, creating false safety. Avoid by tuning thresholds so only genuinely high-risk steps are surfaced.</details>

<details><summary>5. What must every gate define besides approve/reject?</summary>
A timeout behavior (halt or auto-reject) for when the human never responds — otherwise the agent hangs.</details>

---

**Labs:** `1` approval gates → `2` confidence + escalation (with calibration) → `3` feedback loops → `4` multi-agent arbitration. App: `app.py` (real-time step approval UI).

**Next:** [Week 10 Primer](../10_knowledge_graphs/PRIMER.md) — structured reasoning where RAG can't reach.
