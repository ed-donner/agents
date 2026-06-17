"""
Enterprise middleware for production AI agents.

Three independent layers (stack them in any order):
  BudgetMiddleware   — hard-stops spending above per-user or global limits
  PIIScrubber        — redacts personally identifiable information
  AuditLogger        — immutable append-only log for compliance

Usage:
    agent = your_agent_fn
    agent = AuditLogger(PIIScrubber(BudgetMiddleware(agent, budget_usd=1.0)))
    result = agent("user query")

Contract: every wrapped callable MUST accept (prompt, **kwargs). The layers pass
extra kwargs (e.g. user_id) straight through, so the innermost base agent has to
swallow unknown kwargs or it will raise TypeError when called as agent(prompt, user_id=...).
"""

from __future__ import annotations

import json
import re
import time
import uuid
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable


# ---------------------------------------------------------------------------
# Budget Middleware
# ---------------------------------------------------------------------------

# Approximate cost per token (input+output blended) for common models
_BLENDED_COST_PER_TOKEN = {
    "gpt-4o-mini":                0.000000375,   # ~$0.375/1M blended
    "gpt-4o":                     0.00000625,    # ~$6.25/1M blended
    "claude-3-5-haiku-20241022":  0.0000024,     # ~$2.4/1M blended
    "claude-3-5-sonnet-20241022": 0.000009,      # ~$9/1M blended
}

DEFAULT_BLENDED = 0.000002  # conservative default if model unknown


class BudgetExceededError(Exception):
    pass


class BudgetMiddleware:
    """
    Wraps an agent callable and stops it when spending hits a budget.

    Tracks per-user spending via user_id kwarg. Falls back to global budget.
    Raises BudgetExceededError before making the LLM call.
    """

    def __init__(
        self,
        agent_fn: Callable,
        global_budget_usd: float = 10.0,
        per_user_budget_usd: float = 1.0,
        model: str = "gpt-4o-mini",
    ):
        self.agent_fn = agent_fn
        self.global_budget = global_budget_usd
        self.per_user_budget = per_user_budget_usd
        self.cost_per_token = _BLENDED_COST_PER_TOKEN.get(model, DEFAULT_BLENDED)
        self._global_spent: float = 0.0
        self._user_spent: dict[str, float] = defaultdict(float)

    def _estimate_cost(self, prompt: str) -> float:
        # SIMPLIFICATION: this charges a pre-call *estimate* from a word-count
        # heuristic, not the actual token usage. It's adequate for a hard-stop
        # safety cap, but in production charge the real cost from resp.usage
        # AFTER the call (see advanced_evals.pareto_analysis for that pattern),
        # and keep this estimate only for the pre-call "would this exceed?" gate.
        token_estimate = len(prompt.split()) * 1.5 * 2  # input + expected output
        return token_estimate * self.cost_per_token

    def _charge(self, user_id: str, cost: float):
        self._global_spent += cost
        self._user_spent[user_id] += cost

    def __call__(self, prompt: str, user_id: str = "default", **kwargs) -> str:
        estimated = self._estimate_cost(prompt)

        if self._global_spent + estimated > self.global_budget:
            raise BudgetExceededError(
                f"Global budget ${self.global_budget:.2f} would be exceeded "
                f"(spent ${self._global_spent:.4f})"
            )
        if self._user_spent[user_id] + estimated > self.per_user_budget:
            raise BudgetExceededError(
                f"User '{user_id}' budget ${self.per_user_budget:.2f} would be exceeded "
                f"(spent ${self._user_spent[user_id]:.4f})"
            )

        result = self.agent_fn(prompt, **kwargs)
        self._charge(user_id, estimated)
        return result

    def spending_report(self) -> dict:
        return {
            "global_spent_usd": round(self._global_spent, 6),
            "global_budget_usd": self.global_budget,
            "global_remaining_usd": round(self.global_budget - self._global_spent, 6),
            "users": {u: round(s, 6) for u, s in self._user_spent.items()},
        }


# ---------------------------------------------------------------------------
# PII Scrubber
# ---------------------------------------------------------------------------

# Patterns to redact before sending to LLM (and in responses coming back)
_PII_PATTERNS = [
    (re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'), "[EMAIL]"),
    (re.compile(r'\b(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b'), "[PHONE]"),
    (re.compile(r'\b\d{3}[-\s]?\d{2}[-\s]?\d{4}\b'), "[SSN]"),
    (re.compile(r'\b(?:4[0-9]{12}(?:[0-9]{3})?|5[1-5][0-9]{14}|3[47][0-9]{13})\b'), "[CARD]"),
    (re.compile(r'\b\d{1,5}\s+[A-Za-z][\w\s]{5,40}(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Lane|Ln|Drive|Dr|Court|Ct)\b', re.IGNORECASE), "[ADDRESS]"),
    (re.compile(r'\b(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\s+\d{1,2},?\s+\d{4}\b', re.IGNORECASE), "[DATE_OF_BIRTH]"),
]


class PIIScrubber:
    """Redacts PII from prompts before they reach the LLM."""

    def __init__(self, agent_fn: Callable, scrub_response: bool = False):
        self.agent_fn = agent_fn
        self.scrub_response = scrub_response
        self.redaction_count = 0

    def scrub(self, text: str) -> tuple[str, int]:
        count = 0
        for pattern, replacement in _PII_PATTERNS:
            new_text, n = pattern.subn(replacement, text)
            count += n
            text = new_text
        return text, count

    def __call__(self, prompt: str, **kwargs) -> str:
        clean_prompt, n = self.scrub(prompt)
        self.redaction_count += n
        result = self.agent_fn(clean_prompt, **kwargs)
        if self.scrub_response:
            result, _ = self.scrub(result)
        return result


# ---------------------------------------------------------------------------
# Audit Logger
# ---------------------------------------------------------------------------

@dataclass
class AuditEntry:
    entry_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: float = field(default_factory=time.time)
    user_id: str = "unknown"
    prompt_hash: str = ""      # hash only, never log raw prompt in production
    response_preview: str = "" # first 100 chars only
    latency_seconds: float = 0.0
    error: str = ""
    metadata: dict = field(default_factory=dict)


class AuditLogger:
    """
    Append-only audit log for compliance.
    Stores hashes of inputs (not raw PII) and response previews.
    Can write to in-memory list or JSONL file.
    """

    def __init__(self, agent_fn: Callable, log_file: str = ""):
        self.agent_fn = agent_fn
        self.log_file = log_file
        self._log: list[AuditEntry] = []

    def _hash(self, text: str) -> str:
        import hashlib
        return hashlib.sha256(text.encode()).hexdigest()[:16]

    def _write(self, entry: AuditEntry):
        self._log.append(entry)
        if self.log_file:
            with open(self.log_file, "a") as f:
                f.write(json.dumps({
                    "entry_id": entry.entry_id,
                    "timestamp": entry.timestamp,
                    "user_id": entry.user_id,
                    "prompt_hash": entry.prompt_hash,
                    "response_preview": entry.response_preview,
                    "latency_seconds": entry.latency_seconds,
                    "error": entry.error,
                    "metadata": entry.metadata,
                }) + "\n")

    def __call__(self, prompt: str, user_id: str = "anonymous", **kwargs) -> str:
        entry = AuditEntry(
            user_id=user_id,
            prompt_hash=self._hash(prompt),
            metadata={"prompt_length": len(prompt)},
        )
        start = time.monotonic()
        try:
            result = self.agent_fn(prompt, user_id=user_id, **kwargs)
            entry.latency_seconds = time.monotonic() - start
            entry.response_preview = result[:100]
            self._write(entry)
            return result
        except Exception as e:
            entry.latency_seconds = time.monotonic() - start
            entry.error = str(e)
            self._write(entry)
            raise

    def get_log(self) -> list[AuditEntry]:
        return list(self._log)  # immutable copy

    def compliance_summary(self) -> dict:
        total = len(self._log)
        errors = sum(1 for e in self._log if e.error)
        users = len({e.user_id for e in self._log})
        latencies = [e.latency_seconds for e in self._log if not e.error]
        return {
            "total_requests": total,
            "error_count": errors,
            "error_rate": errors / total if total else 0,
            "unique_users": users,
            "avg_latency_seconds": sum(latencies) / len(latencies) if latencies else 0,
        }


# ---------------------------------------------------------------------------
# Demo
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    from openai import OpenAI
    from dotenv import load_dotenv
    load_dotenv(override=True)

    raw_client = OpenAI()

    def base_agent(prompt: str, **kwargs) -> str:
        resp = raw_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=100,
        )
        return resp.choices[0].message.content

    # Stack all three layers
    agent = AuditLogger(PIIScrubber(BudgetMiddleware(base_agent, global_budget_usd=0.10)), log_file="")

    queries = [
        ("user1", "Hello! How do I export my data?"),
        ("user1", "My email is john.doe@example.com and my phone is 555-123-4567. Cancel my account."),
        ("user2", "What is 2+2?"),
    ]

    for user_id, query in queries:
        try:
            result = agent(query, user_id=user_id)
            print(f"[{user_id}] → {result[:80]}")
        except Exception as e:
            print(f"[{user_id}] ERROR: {e}")

    print("\nAudit log:")
    for entry in agent.get_log():
        print(f"  {entry.entry_id[:8]}  user={entry.user_id}  hash={entry.prompt_hash}  lat={entry.latency_seconds:.2f}s  err={entry.error or 'none'}")

    print("\nBudget report:")
    # Access the nested BudgetMiddleware
    print(agent.agent_fn.agent_fn.spending_report())

    print("\nPII redactions:", agent.agent_fn.redaction_count)
    print("\nCompliance summary:", agent.compliance_summary())
