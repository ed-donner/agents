"""Shared message type and helpers for addressing collaborators by registered runtime name."""

from dataclasses import dataclass
import random

from autogen_core import AgentId

# Basenames for modules the Creator will generate (scout.py -> type "scout", etc.)
ROSTER: tuple[str, ...] = ("scout", "synthesizer", "closer")


@dataclass
class Message:
    content: str


def agent_by_name(name: str) -> AgentId:
    """Resolve a collaborator by the same string used in Creator.register(..., name, ...)."""
    if name not in ROSTER:
        raise ValueError(f"Unknown agent name {name!r}; expected one of {ROSTER}")
    return AgentId(name, "default")


def random_peer_excluding(my_type: str) -> AgentId:
    """Pick another collaborator from the roster (for messaging by identity)."""
    others = [n for n in ROSTER if n != my_type]
    if not others:
        return AgentId(my_type, "default")
    return AgentId(random.choice(others), "default")
