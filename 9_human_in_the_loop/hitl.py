"""
Human-in-the-Loop (HITL) framework.

Core abstractions:
  ApprovalGate  — synchronous or async checkpoint requiring human decision
  HITLAgent     — wraps any callable agent step with gate logic
  FeedbackStore — accumulates human corrections for the current session
"""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Optional


class Decision(Enum):
    APPROVE = "approve"
    REJECT = "reject"
    ESCALATE = "escalate"
    TIMEOUT = "timeout"


@dataclass
class Step:
    name: str
    description: str
    payload: Any = None
    confidence: float = 1.0          # 0.0–1.0; below threshold triggers escalation
    requires_approval: bool = True
    cost_estimate_usd: float = 0.0


@dataclass
class ApprovalResult:
    decision: Decision
    feedback: str = ""
    elapsed_seconds: float = 0.0

    @property
    def approved(self) -> bool:
        return self.decision == Decision.APPROVE


@dataclass
class FeedbackStore:
    """Accumulate human corrections within a session."""
    corrections: list[dict] = field(default_factory=list)

    def add(self, step_name: str, original: str, correction: str):
        self.corrections.append({
            "step": step_name,
            "original": original,
            "correction": correction,
            "timestamp": time.time(),
        })

    def as_context(self) -> str:
        if not self.corrections:
            return ""
        lines = ["Previous human corrections in this session:"]
        for c in self.corrections:
            lines.append(f"  [{c['step']}] '{c['original']}' → '{c['correction']}'")
        return "\n".join(lines)


class ApprovalGate:
    """
    Checkpoint that pauses execution and waits for human input.

    Supports three backends:
      - 'cli'     : prompts in the terminal (default, works everywhere)
      - 'auto'    : automatically approves (useful for testing)
      - 'callback': calls a provided function(step) → ApprovalResult
    """

    def __init__(
        self,
        backend: str = "cli",
        timeout_seconds: float = 120.0,
        confidence_threshold: float = 0.7,
        cost_threshold_usd: float = 0.10,
        callback: Optional[Callable[[Step], ApprovalResult]] = None,
    ):
        self.backend = backend
        self.timeout_seconds = timeout_seconds
        self.confidence_threshold = confidence_threshold
        self.cost_threshold_usd = cost_threshold_usd
        self.callback = callback

    def needs_human(self, step: Step) -> bool:
        """Return True if this step requires human approval."""
        if not step.requires_approval:
            return False
        if step.confidence < self.confidence_threshold:
            return True
        if step.cost_estimate_usd > self.cost_threshold_usd:
            return True
        return step.requires_approval

    def request(self, step: Step) -> ApprovalResult:
        """Synchronously request approval for a step."""
        if not self.needs_human(step):
            return ApprovalResult(Decision.APPROVE, feedback="auto-approved (thresholds not triggered)")

        start = time.monotonic()

        if self.backend == "auto":
            return ApprovalResult(Decision.APPROVE, feedback="auto-approved (test mode)")

        if self.backend == "callback" and self.callback:
            result = self.callback(step)
            result.elapsed_seconds = time.monotonic() - start
            return result

        # CLI backend
        return self._cli_prompt(step, start)

    def _cli_prompt(self, step: Step, start: float) -> ApprovalResult:
        print("\n" + "=" * 60)
        print(f"⏸  APPROVAL REQUIRED: {step.name}")
        print(f"   {step.description}")
        if step.confidence < 1.0:
            print(f"   Confidence: {step.confidence:.0%}")
        if step.cost_estimate_usd > 0:
            print(f"   Estimated cost: ${step.cost_estimate_usd:.4f}")
        print("=" * 60)
        print("[a] Approve  [r] Reject  [e] Escalate  [f] Approve with feedback")
        try:
            choice = input("Decision: ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            return ApprovalResult(Decision.TIMEOUT, elapsed_seconds=time.monotonic() - start)

        elapsed = time.monotonic() - start
        if choice == "a":
            return ApprovalResult(Decision.APPROVE, elapsed_seconds=elapsed)
        elif choice == "r":
            reason = input("Reason for rejection: ").strip()
            return ApprovalResult(Decision.REJECT, feedback=reason, elapsed_seconds=elapsed)
        elif choice == "e":
            return ApprovalResult(Decision.ESCALATE, elapsed_seconds=elapsed)
        elif choice == "f":
            feedback = input("Feedback (agent will incorporate): ").strip()
            return ApprovalResult(Decision.APPROVE, feedback=feedback, elapsed_seconds=elapsed)
        else:
            print("Unknown choice — defaulting to ESCALATE")
            return ApprovalResult(Decision.ESCALATE, elapsed_seconds=elapsed)


class HITLAgent:
    """
    Wraps an agent pipeline with approval gates between steps.

    Usage:
        agent = HITLAgent(gate=ApprovalGate(backend='cli'))
        results = agent.run(steps, executor_fn)
    """

    def __init__(self, gate: ApprovalGate, feedback_store: Optional[FeedbackStore] = None):
        self.gate = gate
        self.feedback = feedback_store or FeedbackStore()
        self.run_log: list[dict] = []

    def run(
        self,
        steps: list[Step],
        executor: Callable[[Step, str], Any],
    ) -> list[dict]:
        """
        Execute steps sequentially, pausing at gates.

        Args:
            steps:    List of Step objects defining the workflow.
            executor: fn(step, feedback_context) → result.
                      Called only for approved steps.

        Returns:
            List of dicts with step name, decision, result, and timing.
        """
        results = []
        for step in steps:
            feedback_ctx = self.feedback.as_context()
            approval = self.gate.request(step)

            entry = {
                "step": step.name,
                "decision": approval.decision.value,
                "feedback": approval.feedback,
                "result": None,
                "elapsed_approval": approval.elapsed_seconds,
            }

            if approval.approved:
                if approval.feedback:
                    self.feedback.add(step.name, step.description, approval.feedback)
                    feedback_ctx = self.feedback.as_context()
                entry["result"] = executor(step, feedback_ctx)
            else:
                entry["result"] = f"SKIPPED ({approval.decision.value}): {approval.feedback}"

            self.run_log.append(entry)
            results.append(entry)

            if approval.decision in (Decision.REJECT, Decision.TIMEOUT):
                print(f"\nWorkflow halted at step '{step.name}': {approval.decision.value}")
                break

        return results


# ---------------------------------------------------------------------------
# Demo
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    from openai import OpenAI
    from dotenv import load_dotenv
    load_dotenv(override=True)

    client = OpenAI()

    def llm_executor(step: Step, feedback_context: str) -> str:
        """Simple LLM step executor."""
        messages = [
            {"role": "system", "content": "You are a helpful assistant. Be concise."},
        ]
        if feedback_context:
            messages.append({"role": "user", "content": f"Context from human feedback:\n{feedback_context}"})
        messages.append({"role": "user", "content": step.description})

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            max_tokens=200,
        )
        return response.choices[0].message.content

    STEPS = [
        Step("research", "Summarise the top 3 use cases for AI agents in 2025.", confidence=0.9),
        Step("draft", "Draft a 150-word blog intro about AI agents.", confidence=0.6, cost_estimate_usd=0.02),
        Step("publish", "Post this blog post to the company website.", confidence=0.5, cost_estimate_usd=5.00),
    ]

    gate = ApprovalGate(backend="cli", confidence_threshold=0.7, cost_threshold_usd=0.05)
    agent = HITLAgent(gate=gate)
    results = agent.run(STEPS, llm_executor)

    print("\n\n=== RUN SUMMARY ===")
    for r in results:
        print(f"\n[{r['step']}] {r['decision'].upper()}")
        if r['result']:
            print(r['result'][:300])
