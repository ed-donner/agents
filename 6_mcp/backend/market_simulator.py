"""Simulated share prices for when no market data API key is set.

Generates a believable price for a ticker at a moment in time using smooth value
noise. The price is fully determined by the ticker and the timestamp, so the same
inputs always give the same price, and it wanders gently like a real stock rather
than jumping around randomly.
"""

import hashlib
import math
from datetime import datetime, timezone

EPOCH = datetime(2025, 1, 1, tzinfo=timezone.utc)
SWING = 0.4  # how far the price wanders from its base level, as a fraction
OCTAVES = 5  # layers of noise, from a slow daily trend down to intraday wiggle


def _seed(ticker: str) -> int:
    """A stable integer derived from the ticker, repeatable across processes."""
    digest = hashlib.sha256(ticker.upper().encode()).digest()
    return int.from_bytes(digest[:8], "big")


def _lattice(seed: int, n: int) -> float:
    """A repeatable pseudo-random value in [-1, 1] at integer point n."""
    digest = hashlib.sha256(f"{seed}:{n}".encode()).digest()
    return int.from_bytes(digest[:4], "big") / 0xFFFFFFFF * 2 - 1


def _noise(seed: int, x: float) -> float:
    """Smoothly interpolated noise between the lattice points around x."""
    low = math.floor(x)
    t = x - low
    smooth = t * t * (3 - 2 * t)
    return _lattice(seed, low) * (1 - smooth) + _lattice(seed, low + 1) * smooth


def _wander(seed: int, x: float) -> float:
    """Sum several octaves of noise for a natural trend-plus-wiggle shape."""
    total = 0.0
    normaliser = 0.0
    amplitude = 1.0
    frequency = 1.0
    for _ in range(OCTAVES):
        total += amplitude * _noise(seed, x * frequency)
        normaliser += amplitude
        amplitude /= 2
        frequency *= 2
    return total / normaliser


def simulated_price(ticker: str, when: datetime | None = None) -> float:
    """Return a believable, smoothly varying share price for the ticker."""
    when = when or datetime.now(timezone.utc)
    seed = _seed(ticker)
    base = 20 + seed % 480
    days = (when - EPOCH).total_seconds() / 86400
    return round(base * (1 + SWING * _wander(seed, days)), 2)
