"""
Circuit Breaker pattern for LLM API calls.

States:
  CLOSED   — normal operation, requests flow through
  OPEN     — too many failures, requests fail fast without calling the API
  HALF_OPEN — testing if the service has recovered (allow one request through)

Why this matters: if OpenAI/Anthropic has an outage, without a circuit breaker
your agent will queue up thousands of slow-failing requests, exhausting threads
and budgets. With a circuit breaker, it fails fast and recovers gracefully.
"""

from __future__ import annotations

import time
from enum import Enum
from typing import Callable, Optional


class CircuitState(Enum):
    CLOSED = "closed"       # healthy
    OPEN = "open"           # tripped, failing fast
    HALF_OPEN = "half_open" # testing recovery


class CircuitBreakerError(Exception):
    pass


class CircuitBreaker:
    """
    Wraps any callable with circuit breaker logic.

    Args:
        fn:                  The function to protect (e.g. an LLM call)
        failure_threshold:   Number of consecutive failures before opening
        recovery_timeout:    Seconds to wait before trying HALF_OPEN
        success_threshold:   Consecutive successes needed to close from HALF_OPEN
        fallback:            Optional callable to use when circuit is OPEN
    """

    def __init__(
        self,
        fn: Callable,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0,
        success_threshold: int = 2,
        fallback: Optional[Callable] = None,
    ):
        self.fn = fn
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.success_threshold = success_threshold
        self.fallback = fallback

        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._last_failure_time: float = 0.0
        self._total_calls = 0
        self._total_failures = 0
        self._total_short_circuits = 0

    @property
    def state(self) -> CircuitState:
        if self._state == CircuitState.OPEN:
            if time.monotonic() - self._last_failure_time >= self.recovery_timeout:
                self._state = CircuitState.HALF_OPEN
                self._success_count = 0
        return self._state

    def __call__(self, *args, **kwargs):
        self._total_calls += 1
        current_state = self.state

        if current_state == CircuitState.OPEN:
            self._total_short_circuits += 1
            if self.fallback:
                return self.fallback(*args, **kwargs)
            raise CircuitBreakerError(
                f"Circuit OPEN — service unavailable (will retry after {self.recovery_timeout}s)"
            )

        try:
            result = self.fn(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise

    def _on_success(self):
        self._failure_count = 0
        if self._state == CircuitState.HALF_OPEN:
            self._success_count += 1
            if self._success_count >= self.success_threshold:
                self._state = CircuitState.CLOSED
                print(f"[CircuitBreaker] CLOSED — service recovered")

    def _on_failure(self):
        self._total_failures += 1
        self._failure_count += 1
        self._last_failure_time = time.monotonic()

        if self._failure_count >= self.failure_threshold:
            if self._state != CircuitState.OPEN:
                self._state = CircuitState.OPEN
                print(f"[CircuitBreaker] OPEN — {self._failure_count} failures, failing fast for {self.recovery_timeout}s")

    def stats(self) -> dict:
        return {
            "state": self.state.value,
            "total_calls": self._total_calls,
            "total_failures": self._total_failures,
            "total_short_circuits": self._total_short_circuits,
            "failure_count": self._failure_count,
            "failure_rate": self._total_failures / self._total_calls if self._total_calls else 0,
        }

    def reset(self):
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0


# ---------------------------------------------------------------------------
# Demo
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    from openai import OpenAI
    from dotenv import load_dotenv
    load_dotenv(override=True)

    client = OpenAI()
    call_count = [0]

    def flaky_llm(prompt: str) -> str:
        """Simulates an LLM that fails every 3rd call."""
        call_count[0] += 1
        if call_count[0] % 3 == 0:
            raise ConnectionError("Simulated LLM timeout")
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=50,
        )
        return resp.choices[0].message.content

    def fallback(prompt: str) -> str:
        return "Service temporarily unavailable. Please try again later."

    cb = CircuitBreaker(
        fn=flaky_llm,
        failure_threshold=2,
        recovery_timeout=5.0,
        fallback=fallback,
    )

    print("Sending 8 requests to flaky LLM with circuit breaker...\n")
    for i in range(8):
        try:
            result = cb(f"Request {i+1}: What is {i}+{i}?")
            print(f"Request {i+1}: {result[:60]}")
        except CircuitBreakerError as e:
            print(f"Request {i+1}: CIRCUIT OPEN — {e}")
        except Exception as e:
            print(f"Request {i+1}: ERROR — {e}")
        print(f"  State: {cb.stats()['state']}")

    print(f"\nFinal stats: {cb.stats()}")
