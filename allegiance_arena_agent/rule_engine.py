from __future__ import annotations

from .config import ArenaConfig
from .memory import MemoryStore
from .models import VoteDecision, VoteOptionScore


class RuleEngine:
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

    def _leader_state(self, memory: MemoryStore) -> tuple[str | None, float]:
        scores = self._latest_scores(memory)
        if not scores:
            return (None, 0.0)
        leader_name, leader_score = max(scores.items(), key=lambda item: item[1])
        my_score = float(scores.get(memory.me, 0.0))
        return (leader_name, max(0.0, leader_score - my_score))

    def validate_vote_options(
        self,
        memory: MemoryStore,
        options: list[VoteOptionScore],
    ) -> list[VoteOptionScore]:
        filtered: list[VoteOptionScore] = []
        for option in options:
            if option.target is None:
                continue
            if option.target == memory.me:
                continue
            stats = memory.agents.get(option.target)
            if stats and stats.betrayal_count >= 3 and option.components.get("p_coop", 0.0) < 0.4:
                # Hard guard against repeated betrayal loops.
                continue
            if stats and stats.trust_score < -3.0:
                continue
            filtered.append(option)
        return filtered

    @staticmethod
    def _first_non_self_target(memory: MemoryStore, options: list[VoteOptionScore]) -> str | None:
        for option in options:
            if option.target and option.target != memory.me:
                return option.target
        for name in sorted(memory.agents.keys()):
            if name != memory.me:
                return name
        return None

    def finalize_vote(self, memory: MemoryStore, options: list[VoteOptionScore]) -> VoteDecision:
        valid = self.validate_vote_options(memory, options)
        if not valid:
            forced_target = self._first_non_self_target(memory, options)
            if forced_target is None:
                return VoteDecision(
                    target=None,
                    reason="No available non-self target found.",
                    expected_value=0.0,
                    source="rule_engine",
                )
            return VoteDecision(
                target=forced_target,
                reason=(
                    f"No safe option passed constraints; forced vote for {forced_target} "
                    "to avoid abstain."
                ),
                expected_value=0.0,
                source="rule_engine",
            )

        leader_name, leader_gap = self._leader_state(memory)
        if (
            self.config.avoid_leader_when_behind
            and leader_name
            and leader_gap >= self.config.leader_gap_activation
            and valid[0].target == leader_name
        ):
            best = valid[0]
            alternatives = [opt for opt in valid if opt.target != leader_name]
            alternatives.sort(key=lambda item: item.expected_value, reverse=True)
            min_required_ev = max(
                self.config.catchup_min_ev,
                best.expected_value - self.config.catchup_ev_delta_max,
            )
            for alt in alternatives:
                if alt.expected_value >= min_required_ev:
                    return VoteDecision(
                        target=alt.target,
                        reason=(
                            f"Catch-up override: trailing leader {leader_name} by {leader_gap:.1f}; "
                            f"avoiding leader target and selecting {alt.target} "
                            f"(EV={alt.expected_value:.2f}, threshold={min_required_ev:.2f})."
                        ),
                        expected_value=alt.expected_value,
                        source="rule_engine",
                    )

        best = valid[0]
        return VoteDecision(
            target=best.target,
            reason=(
                f"Selected {best.target} (no-abstain mode): EV={best.expected_value:.2f}, "
                f"risk={best.risk:.2f}, p_coop={best.components.get('p_coop', 0.0):.2f}"
            ),
            expected_value=best.expected_value,
            source="rule_engine",
        )
