from __future__ import annotations

import random
from dataclasses import dataclass

from .config import ArenaConfig
from .memory import MemoryStore
from .models import OpponentProfile, VoteOptionScore


@dataclass(slots=True)
class SimulationContext:
    me: str
    round_number: int
    candidates: list[str]


class SimulationEngine:
    def __init__(self, config: ArenaConfig) -> None:
        self.config = config

    @staticmethod
    def _latest_scores(memory: MemoryStore) -> dict[str, float]:
        for record in reversed(memory.round_records):
            scores_after = record.raw_results.get("scores_after")
            if isinstance(scores_after, dict) and scores_after:
                parsed: dict[str, float] = {}
                for name, score in scores_after.items():
                    try:
                        parsed[str(name)] = float(score)
                    except (TypeError, ValueError):
                        continue
                if parsed:
                    return parsed
        return {}

    def _leader_state(self, memory: MemoryStore) -> tuple[str | None, float, float]:
        scores = self._latest_scores(memory)
        if not scores:
            return (None, 0.0, 0.0)
        leader_name, leader_score = max(scores.items(), key=lambda item: item[1])
        my_score = float(scores.get(memory.me, 0.0))
        return (leader_name, my_score, float(leader_score))

    @staticmethod
    def _cooperation_probability(
        trust_score: float,
        profile: OpponentProfile | None,
        confidence_floor: float = 0.3,
    ) -> float:
        trust_term = 0.45 + (trust_score / 14.0)
        label_term = 0.0
        if profile:
            raw_label_term = {
                "cooperator": 0.22,
                "tit_for_tat": 0.14,
                "opportunist": -0.10,
                "defector": -0.26,
                "unknown": 0.0,
            }.get(profile.label, 0.0)
            confidence = max(confidence_floor, min(1.0, float(profile.confidence)))
            label_term = raw_label_term * confidence
            label_term += (profile.reciprocity_rate - profile.exploitation_rate) * 0.2
        return max(0.03, min(0.95, trust_term + label_term))

    @staticmethod
    def _payoff_when_i_vote_target(target_cooperates: bool, received_any_vote: bool) -> float:
        if target_cooperates:
            return 5.0
        if received_any_vote:
            return 3.0  # one-way received (best non-mutual rescue)
        return -2.0  # isolation

    def _estimate_other_vote_support(self, memory: MemoryStore, target: str) -> float:
        supporters = 0.0
        total = 0.0
        for name, stats in memory.agents.items():
            if name == target:
                continue
            total += 1.0
            if getattr(stats, "last_vote_target", None) == target:
                supporters += 1.0
            supporters += min(max(stats.cooperation_rate - 0.3, 0.0), 0.7)
        if total == 0:
            return 0.2
        return max(0.05, min(0.9, supporters / total))

    def score_target(self, memory: MemoryStore, target: str) -> VoteOptionScore:
        stats = memory.agents.get(target) or memory.ensure_agent(target)
        profile = memory.opponent_profiles.get(target)
        p_coop = self._cooperation_probability(
            stats.trust_score,
            profile,
            confidence_floor=self.config.profile_confidence_floor,
        )
        p_received = self._estimate_other_vote_support(memory, target)
        leader_name, my_score, leader_score = self._leader_state(memory)
        leader_gap = max(0.0, leader_score - my_score)
        is_leader_target = bool(leader_name and target == leader_name)

        if not self.config.simulation_enabled_monte_carlo:
            ev = (
                p_coop * self._payoff_when_i_vote_target(True, p_received > 0.35)
                + (1 - p_coop) * self._payoff_when_i_vote_target(False, p_received > 0.35)
            )
        else:
            total = 0.0
            runs = max(10, self.config.simulation_runs)
            for _ in range(runs):
                coop = random.random() < p_coop
                received_any = random.random() < p_received
                total += self._payoff_when_i_vote_target(coop, received_any)
            ev = total / runs

        risk = max(0.0, 1.0 - p_coop) + max(0.0, 0.25 - p_received)
        risk = min(2.0, risk)
        adjusted_ev = ev - (risk * self.config.risk_penalty_weight)
        isolation_support_bonus = max(0.0, p_received - 0.35) * self.config.isolation_support_bonus_weight
        adjusted_ev += isolation_support_bonus

        competitive_penalty = 0.0
        if (
            self.config.avoid_leader_when_behind
            and is_leader_target
            and leader_gap >= self.config.leader_gap_activation
        ):
            pressure = leader_gap / max(self.config.leader_gap_activation, 1.0)
            if 0 < memory.current_round <= self.config.fast_start_rounds:
                pressure *= 1.15
            competitive_penalty = min(2.5, pressure * self.config.leader_target_penalty_weight)
            adjusted_ev -= competitive_penalty

        return VoteOptionScore(
            target=target,
            expected_value=round(adjusted_ev, 4),
            risk=round(risk, 4),
            components={
                "p_coop": round(p_coop, 4),
                "p_received": round(p_received, 4),
                "base_ev": round(ev, 4),
                "risk_penalty": round(risk * self.config.risk_penalty_weight, 4),
                "isolation_support_bonus": round(isolation_support_bonus, 4),
                "leader_gap": round(leader_gap, 4),
                "is_leader_target": 1.0 if is_leader_target else 0.0,
                "competitive_penalty": round(competitive_penalty, 4),
            },
        )

    def rank_options(self, memory: MemoryStore, candidates: list[str]) -> list[VoteOptionScore]:
        scores = [self.score_target(memory, target) for target in candidates if target != memory.me]
        scores.sort(key=lambda item: item.expected_value, reverse=True)
        return scores
