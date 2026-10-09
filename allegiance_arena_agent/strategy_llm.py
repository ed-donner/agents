from __future__ import annotations

from typing import Any

from .config import ArenaConfig
from .model_router import LLMResult, ModelRouter
from .models import LLMPlan


class LLMStrategyAgent:
    def __init__(self, config: ArenaConfig, router: ModelRouter) -> None:
        self.config = config
        self.router = router

    def _build_planning_messages(
        self,
        *,
        me: str,
        round_number: int,
        phase: str,
        incoming_messages: list[dict[str, Any]],
        trust_rows: list[dict[str, Any]],
        candidates: list[str],
        leaderboard_rows: list[dict[str, Any]],
    ) -> list[dict[str, str]]:
        system = (
            "You are a strategic alliance planner for Allegiance Arena. "
            "Return strict JSON only with keys: ranked_targets (array), direct_messages (array of {target,message}), "
            "broadcast_message (string or null), behavior_predictions (object). "
            "Prioritize reciprocal +5 mutual outcomes, avoid obvious defectors, and avoid feeding the current #1 "
            "when a catch-up path exists. Favor coalition messages that redirect support away from a runaway leader. "
            "For early rounds, optimize for fast-start momentum and durable non-leader pacts. "
            "Always produce at least two primary reciprocity pacts and one backup pact if enough candidates exist."
        )
        user = {
            "me": me,
            "round": round_number,
            "phase": phase,
            "candidates": candidates[:10],
            "incoming_messages": incoming_messages[-20:],
            "trust_rows": trust_rows[:12],
            "leaderboard": leaderboard_rows[:12],
            "constraints": {
                "max_direct_messages": self.config.max_direct_messages_per_diplomacy,
                "cannot_vote_self": True,
                "must_be_concise": True,
                "min_primary_pacts": self.config.min_primary_pacts,
                "min_backup_pacts": self.config.min_backup_pacts,
            },
        }
        return [{"role": "system", "content": system}, {"role": "user", "content": str(user)}]

    @staticmethod
    def _dedupe_messages(messages: list[tuple[str, str]]) -> list[tuple[str, str]]:
        seen: set[str] = set()
        deduped: list[tuple[str, str]] = []
        for target, message in messages:
            if target in seen:
                continue
            seen.add(target)
            deduped.append((target, message))
        return deduped

    def _ensure_minimum_pacts(
        self,
        *,
        direct_messages: list[tuple[str, str]],
        ranked_targets: list[str],
        candidates: list[str],
        leader_name: str | None,
    ) -> list[tuple[str, str]]:
        base = self._dedupe_messages(direct_messages)
        selected = {target for target, _ in base}

        ordered_targets = [t for t in ranked_targets if t in candidates]
        ordered_targets.extend([t for t in candidates if t not in ordered_targets])
        non_leader_pool = [t for t in ordered_targets if t != leader_name]
        primary_needed = max(0, self.config.min_primary_pacts)
        backup_needed = max(0, self.config.min_backup_pacts)

        for target in non_leader_pool:
            if primary_needed <= 0:
                break
            if target in selected:
                primary_needed -= 1
                continue
            base.append(
                (
                    target,
                    f"{target}, primary pact: mutual vote with me this round for guaranteed +5 each. Confirm?",
                )
            )
            selected.add(target)
            primary_needed -= 1

        for target in non_leader_pool:
            if backup_needed <= 0:
                break
            if target in selected:
                continue
            base.append(
                (
                    target,
                    (
                        f"{target}, backup pact: if my main mutual falls through, "
                        "let's switch to each other this round for +5."
                    ),
                )
            )
            selected.add(target)
            backup_needed -= 1

        return base

    def plan_diplomacy(
        self,
        *,
        me: str,
        round_number: int,
        phase: str,
        incoming_messages: list[dict[str, Any]],
        trust_rows: list[dict[str, Any]],
        candidates: list[str],
        leaderboard_rows: list[dict[str, Any]],
    ) -> tuple[LLMPlan, LLMResult]:
        response = self.router.generate(
            component="strategy_planning",
            phase=phase,
            messages=self._build_planning_messages(
                me=me,
                round_number=round_number,
                phase=phase,
                incoming_messages=incoming_messages,
                trust_rows=trust_rows,
                candidates=candidates,
                leaderboard_rows=leaderboard_rows,
            ),
            primary=self.config.strategy_primary,
            backup=self.config.strategy_backup,
            temperature=0.25,
        )
        payload = self.router.parse_json_object(response.text)
        ranked_targets = [str(x) for x in payload.get("ranked_targets", []) if str(x).strip()]
        direct_messages: list[tuple[str, str]] = []
        for item in payload.get("direct_messages", []):
            if not isinstance(item, dict):
                continue
            target = str(item.get("target", "")).strip()
            message = str(item.get("message", "")).strip()
            if target and message:
                direct_messages.append((target, message[:500]))
        broadcast = payload.get("broadcast_message")
        broadcast_message = str(broadcast)[:500] if isinstance(broadcast, str) and broadcast.strip() else None
        behavior_predictions = (
            payload.get("behavior_predictions")
            if isinstance(payload.get("behavior_predictions"), dict)
            else {}
        )
        leader_name = None
        if leaderboard_rows and isinstance(leaderboard_rows[0], dict):
            top_name = leaderboard_rows[0].get("name")
            if isinstance(top_name, str):
                leader_name = top_name

        if not ranked_targets:
            ranked_targets = candidates[:]
        if not direct_messages:
            for target in ranked_targets[: self.config.max_direct_messages_per_diplomacy]:
                direct_messages.append(
                    (
                        target,
                        f"{target}, let's coordinate a reciprocal vote for mutual +5 this round.",
                    )
                )
        direct_messages = self._ensure_minimum_pacts(
            direct_messages=direct_messages,
            ranked_targets=ranked_targets,
            candidates=candidates,
            leader_name=leader_name,
        )

        return (
            LLMPlan(
                ranked_targets=ranked_targets,
                direct_messages=direct_messages[:10],
                broadcast_message=broadcast_message,
                behavior_predictions={
                    str(k): str(v)[:120] for k, v in behavior_predictions.items()
                },
                raw=payload,
            ),
            response,
        )

    def generate_message_fallback(
        self,
        *,
        me: str,
        phase: str,
        target: str,
        intent: str,
    ) -> tuple[str, LLMResult]:
        response = self.router.generate(
            component="messaging",
            phase=phase,
            primary=self.config.messaging_primary,
            backup=self.config.messaging_backup,
            temperature=0.35,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Write a concise diplomacy DM for Allegiance Arena. "
                        "Under 220 chars. No markdown."
                    ),
                },
                {
                    "role": "user",
                    "content": str(
                        {
                            "sender": me,
                            "target": target,
                            "intent": intent,
                        }
                    ),
                },
            ],
        )
        text = response.text.strip().replace("\n", " ")
        if len(text) > 500:
            text = text[:500]
        return text, response
