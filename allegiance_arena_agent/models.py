from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(slots=True)
class AgentStats:
    name: str
    votes_given: int = 0
    votes_received: int = 0
    votes_to_me: int = 0
    votes_from_me: int = 0
    cooperation_rate: float = 0.0
    betrayal_count: int = 0
    current_alliance_streak: int = 0
    trust_score: float = 0.0
    rounds_observed: int = 0
    last_vote_target: str | None = None
    recent_votes: list[str | None] = field(default_factory=list)
    commitments_kept: int = 0
    commitments_broken: int = 0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "AgentStats":
        return cls(**payload)


@dataclass(slots=True)
class OpponentProfile:
    name: str
    label: str = "unknown"
    confidence: float = 0.0
    rationale: str = "insufficient evidence"
    switch_rate: float = 0.0
    reciprocity_rate: float = 0.0
    exploitation_rate: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "OpponentProfile":
        return cls(**payload)


@dataclass(slots=True)
class RoundRecord:
    round_number: int
    votes: dict[str, str | None] = field(default_factory=dict)
    alliances: list[tuple[str, str]] = field(default_factory=list)
    leaderboard: list[dict[str, Any]] = field(default_factory=list)
    raw_results: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["alliances"] = [list(pair) for pair in self.alliances]
        return data

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "RoundRecord":
        alliances = [
            (str(item[0]), str(item[1]))
            for item in payload.get("alliances", [])
            if isinstance(item, (list, tuple)) and len(item) == 2
        ]
        return cls(
            round_number=int(payload["round_number"]),
            votes=dict(payload.get("votes", {})),
            alliances=alliances,
            leaderboard=list(payload.get("leaderboard", [])),
            raw_results=dict(payload.get("raw_results", {})),
        )


@dataclass(slots=True)
class LLMPlan:
    ranked_targets: list[str]
    direct_messages: list[tuple[str, str]]
    broadcast_message: str | None
    behavior_predictions: dict[str, str] = field(default_factory=dict)
    raw: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class VoteOptionScore:
    target: str | None
    expected_value: float
    risk: float
    components: dict[str, float] = field(default_factory=dict)


@dataclass(slots=True)
class VoteDecision:
    target: str | None
    reason: str
    expected_value: float
    source: str = "rules+simulation"
