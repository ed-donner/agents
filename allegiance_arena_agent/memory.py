from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .models import AgentStats, OpponentProfile, RoundRecord


class MemoryStore:
    def __init__(self, me: str, trust_decay: float = 0.92, path: str | None = None) -> None:
        self.me = me
        self.trust_decay = trust_decay
        self.path = Path(path) if path else None
        self.current_round: int = 0
        self.current_phase: str = "unknown"
        self.current_ally: str | None = None
        self.last_vote_target: str | None = None
        self.pending_commitments: set[str] = set()
        self.agents: dict[str, AgentStats] = {}
        self.opponent_profiles: dict[str, OpponentProfile] = {}
        self.round_records: list[RoundRecord] = []

    def ensure_agent(self, name: str) -> AgentStats:
        if name == self.me:
            raise ValueError("Self should not be tracked as external agent.")
        if name not in self.agents:
            self.agents[name] = AgentStats(name=name)
        if name not in self.opponent_profiles:
            self.opponent_profiles[name] = OpponentProfile(name=name)
        return self.agents[name]

    def note_commitment(self, name: str) -> None:
        if name and name != self.me:
            self.pending_commitments.add(name)

    def clear_commitments(self) -> None:
        self.pending_commitments.clear()

    @staticmethod
    def _parse_votes(raw: Any) -> dict[str, str | None]:
        if isinstance(raw, dict):
            if isinstance(raw.get("votes"), dict):
                return {
                    str(voter): (str(target) if target not in {"", None} else None)
                    for voter, target in raw["votes"].items()
                }
            if isinstance(raw.get("pledges"), dict):
                return {
                    str(voter): (str(target) if target not in {"", None} else None)
                    for voter, target in raw["pledges"].items()
                }
            nested = raw.get("round")
            if isinstance(nested, dict):
                return MemoryStore._parse_votes(nested)
        return {}

    @staticmethod
    def _parse_alliances(raw: Any) -> list[tuple[str, str]]:
        parsed: list[tuple[str, str]] = []
        if isinstance(raw, dict) and isinstance(raw.get("alliances"), list):
            raw = raw["alliances"]
        if isinstance(raw, list):
            for item in raw:
                if isinstance(item, dict):
                    agents = item.get("agents")
                    if isinstance(agents, list) and len(agents) == 2:
                        parsed.append((str(agents[0]), str(agents[1])))
                        continue
                    a = item.get("a") or item.get("agent_a")
                    b = item.get("b") or item.get("agent_b")
                    if a and b:
                        parsed.append((str(a), str(b)))
                elif isinstance(item, (list, tuple)) and len(item) == 2:
                    parsed.append((str(item[0]), str(item[1])))
        return parsed

    def _decay_trust(self) -> None:
        for stats in self.agents.values():
            stats.trust_score *= self.trust_decay

    def update_after_round(
        self,
        round_number: int,
        round_results: Any,
        alliances: Any,
        leaderboard: Any,
    ) -> None:
        votes = self._parse_votes(round_results)
        if not votes:
            return

        self._decay_trust()
        my_target = votes.get(self.me)
        for voter, target in votes.items():
            if voter == self.me:
                continue
            stats = self.ensure_agent(voter)
            stats.rounds_observed += 1
            stats.votes_given += 1
            target = target if target else None
            stats.last_vote_target = target
            stats.recent_votes.append(target)
            stats.recent_votes = stats.recent_votes[-6:]

            if target == self.me:
                stats.votes_to_me += 1
                stats.votes_received += 1
                stats.trust_score += 1.6
                if my_target == voter:
                    stats.current_alliance_streak += 1
                    stats.trust_score += 1.1
                else:
                    stats.current_alliance_streak = 0
            else:
                if my_target == voter:
                    stats.betrayal_count += 1
                    stats.current_alliance_streak = 0
                    stats.trust_score -= 2.0
                elif target is not None:
                    stats.trust_score -= 0.25

            if voter in self.pending_commitments:
                if target == self.me:
                    stats.commitments_kept += 1
                    stats.trust_score += 0.7
                else:
                    stats.commitments_broken += 1
                    stats.betrayal_count += 1
                    stats.trust_score -= 1.2

            stats.cooperation_rate = stats.votes_to_me / max(stats.rounds_observed, 1)

        if my_target and my_target != self.me and votes.get(my_target) == self.me:
            self.current_ally = my_target
        else:
            self.current_ally = None

        record = RoundRecord(
            round_number=round_number,
            votes=votes,
            alliances=self._parse_alliances(alliances),
            leaderboard=list(leaderboard if isinstance(leaderboard, list) else []),
            raw_results=dict(round_results if isinstance(round_results, dict) else {}),
        )
        self.round_records.append(record)
        self.clear_commitments()

    def to_dict(self) -> dict[str, Any]:
        return {
            "me": self.me,
            "trust_decay": self.trust_decay,
            "current_round": self.current_round,
            "current_phase": self.current_phase,
            "current_ally": self.current_ally,
            "last_vote_target": self.last_vote_target,
            "pending_commitments": sorted(self.pending_commitments),
            "agents": {k: v.to_dict() for k, v in self.agents.items()},
            "opponent_profiles": {k: v.to_dict() for k, v in self.opponent_profiles.items()},
            "round_records": [record.to_dict() for record in self.round_records],
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any], path: str | None = None) -> "MemoryStore":
        store = cls(me=str(payload["me"]), trust_decay=float(payload.get("trust_decay", 0.92)), path=path)
        store.current_round = int(payload.get("current_round", 0))
        store.current_phase = str(payload.get("current_phase", "unknown"))
        store.current_ally = payload.get("current_ally")
        store.last_vote_target = payload.get("last_vote_target")
        store.pending_commitments = set(payload.get("pending_commitments", []))
        store.agents = {
            k: AgentStats.from_dict(v) for k, v in dict(payload.get("agents", {})).items()
        }
        store.opponent_profiles = {
            k: OpponentProfile.from_dict(v)
            for k, v in dict(payload.get("opponent_profiles", {})).items()
        }
        store.round_records = [
            RoundRecord.from_dict(item) for item in list(payload.get("round_records", []))
        ]
        return store

    def save(self) -> None:
        if not self.path:
            return
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(self.to_dict(), indent=2), encoding="utf-8")

    @classmethod
    def load(cls, me: str, trust_decay: float, path: str | None = None) -> "MemoryStore":
        if not path:
            return cls(me=me, trust_decay=trust_decay)
        file_path = Path(path)
        if not file_path.exists():
            return cls(me=me, trust_decay=trust_decay, path=path)
        try:
            data = json.loads(file_path.read_text(encoding="utf-8"))
            return cls.from_dict(data, path=path)
        except (json.JSONDecodeError, OSError, KeyError, TypeError, ValueError):
            return cls(me=me, trust_decay=trust_decay, path=path)
