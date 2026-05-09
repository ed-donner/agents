from __future__ import annotations

from typing import Any

from .config import ArenaConfig
from .memory import MemoryStore
from .model_router import LLMResult, ModelRouter
from .models import OpponentProfile

VALID_LABELS = {"cooperator", "defector", "opportunist", "tit_for_tat", "unknown"}


class OpponentModelingAgent:
    def __init__(self, config: ArenaConfig, router: ModelRouter) -> None:
        self.config = config
        self.router = router

    @staticmethod
    def _safe_rate(numerator: float, denominator: float) -> float:
        if denominator <= 0:
            return 0.0
        return numerator / denominator

    def _heuristic_profile(self, memory: MemoryStore, name: str) -> OpponentProfile:
        stats = memory.agents.get(name) or memory.ensure_agent(name)
        recent = stats.recent_votes[-5:]
        switch_count = 0
        for idx in range(1, len(recent)):
            if recent[idx] != recent[idx - 1]:
                switch_count += 1
        switch_rate = self._safe_rate(switch_count, max(len(recent) - 1, 1))
        reciprocity_rate = stats.cooperation_rate
        exploitation_rate = self._safe_rate(stats.betrayal_count, max(stats.rounds_observed, 1))

        label = "unknown"
        confidence = 0.35
        rationale = "Limited evidence."
        if stats.rounds_observed >= 2:
            if reciprocity_rate >= 0.55 and exploitation_rate < 0.20:
                label = "cooperator"
                confidence = min(0.9, 0.55 + reciprocity_rate * 0.35)
                rationale = "Consistent reciprocal support."
            elif exploitation_rate >= 0.45:
                label = "defector"
                confidence = min(0.9, 0.55 + exploitation_rate * 0.35)
                rationale = "High betrayal / low reciprocity pattern."
            elif switch_rate >= 0.55:
                label = "opportunist"
                confidence = min(0.85, 0.5 + switch_rate * 0.4)
                rationale = "Frequently changes allegiance targets."
            elif 0.25 <= switch_rate <= 0.5 and stats.betrayal_count <= 1:
                label = "tit_for_tat"
                confidence = min(0.8, 0.45 + (1 - abs(0.35 - switch_rate)) * 0.3)
                rationale = "Reactive behavior with moderate switching."

        return OpponentProfile(
            name=name,
            label=label,
            confidence=round(confidence, 3),
            rationale=rationale,
            switch_rate=round(switch_rate, 3),
            reciprocity_rate=round(reciprocity_rate, 3),
            exploitation_rate=round(exploitation_rate, 3),
        )

    def _llm_refine(
        self,
        *,
        phase: str,
        profile: OpponentProfile,
        stats_blob: dict[str, Any],
    ) -> tuple[OpponentProfile, LLMResult | None]:
        try:
            response = self.router.generate(
                component="opponent_modeling",
                phase=phase,
                primary=self.config.opponent_primary,
                backup=self.config.opponent_backup,
                temperature=0.15,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "Classify opponent behavior for Allegiance Arena. "
                            "Return JSON: {label, confidence, rationale}. "
                            "label must be one of cooperator, defector, opportunist, tit_for_tat, unknown."
                        ),
                    },
                    {"role": "user", "content": str({"profile": profile.to_dict(), "stats": stats_blob})},
                ],
            )
        except Exception:
            return profile, None

        parsed = self.router.parse_json_object(response.text)
        label = str(parsed.get("label", profile.label)).strip().lower()
        if label not in VALID_LABELS:
            label = profile.label
        confidence = parsed.get("confidence", profile.confidence)
        try:
            confidence = float(confidence)
        except (TypeError, ValueError):
            confidence = profile.confidence
        confidence = max(0.0, min(1.0, confidence))
        rationale = str(parsed.get("rationale", profile.rationale))[:180]
        return (
            OpponentProfile(
                name=profile.name,
                label=label,
                confidence=round(confidence, 3),
                rationale=rationale,
                switch_rate=profile.switch_rate,
                reciprocity_rate=profile.reciprocity_rate,
                exploitation_rate=profile.exploitation_rate,
            ),
            response,
        )

    def update_profiles(self, memory: MemoryStore, phase: str) -> dict[str, OpponentProfile]:
        updated: dict[str, OpponentProfile] = {}
        for name in sorted(memory.agents.keys()):
            heuristic = self._heuristic_profile(memory, name)
            stats = memory.agents[name].to_dict()
            refined, _ = self._llm_refine(phase=phase, profile=heuristic, stats_blob=stats)
            memory.opponent_profiles[name] = refined
            updated[name] = refined
        return updated
