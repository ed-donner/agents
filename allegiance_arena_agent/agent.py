from __future__ import annotations

import logging
import time
from typing import Any

from .config import ArenaConfig
from .mcp_client import ArenaMCPClient, MCPClientError
from .memory import MemoryStore
from .model_router import ModelRouter
from .opponent_model import OpponentModelingAgent
from .rule_engine import RuleEngine
from .simulation import SimulationEngine
from .strategy_llm import LLMStrategyAgent


class CompetitiveArenaCoordinator:
    def __init__(self, config: ArenaConfig) -> None:
        self.config = config
        self.logger = logging.getLogger(self.__class__.__name__)
        self.client = ArenaMCPClient(
            endpoint=config.endpoint,
            timeout_seconds=config.mcp_timeout_seconds,
            max_retries=config.mcp_max_retries,
            retry_backoff_seconds=config.mcp_retry_backoff_seconds,
        )
        self.memory = MemoryStore.load(
            me=config.agent_name,
            trust_decay=config.trust_decay,
            path=config.memory_path,
        )
        self.router = ModelRouter(config)
        self.llm_strategy = LLMStrategyAgent(config, self.router)
        self.opponent_modeler = OpponentModelingAgent(config, self.router)
        self.simulator = SimulationEngine(config)
        self.rule_engine = RuleEngine(config)
        self.executed_phase_actions: set[tuple[int, str]] = set()
        self.rounds_updated: set[int] = set()
        self._tick_counter: int = 0

    @staticmethod
    def _parse_round(game_state: Any) -> int:
        if isinstance(game_state, dict):
            for key in ("round", "current_round", "round_number"):
                if key in game_state:
                    try:
                        return int(game_state[key])
                    except (TypeError, ValueError):
                        continue
        return 0

    @staticmethod
    def _parse_phase(game_state: Any) -> str:
        if not isinstance(game_state, dict):
            return "unknown"
        return str(game_state.get("phase") or game_state.get("current_phase") or game_state.get("state") or "unknown").lower()

    @staticmethod
    def _parse_status(game_state: Any) -> str:
        if not isinstance(game_state, dict):
            return "unknown"
        return str(game_state.get("status") or "").lower()

    @staticmethod
    def _parse_game_over(game_state: Any) -> bool:
        if not isinstance(game_state, dict):
            return False
        if str(game_state.get("status", "")).lower() == "ended":
            return True
        for key in ("game_over", "finished", "done", "is_over"):
            if key in game_state and bool(game_state[key]):
                return True
        return False

    @staticmethod
    def _extract_players(game_state: Any) -> list[str]:
        if not isinstance(game_state, dict):
            return []
        raw = game_state.get("players")
        if not isinstance(raw, list):
            return []
        names: list[str] = []
        for item in raw:
            if isinstance(item, dict):
                name = item.get("name")
                if isinstance(name, str) and name.strip():
                    names.append(name.strip())
        return names

    @staticmethod
    def _state_summary(game_state: Any) -> dict[str, Any]:
        if not isinstance(game_state, dict):
            return {"raw_type": type(game_state).__name__}
        keys = (
            "status",
            "phase",
            "current_phase",
            "state",
            "round",
            "current_round",
            "round_number",
            "time_remaining",
            "seconds_left",
            "diplomacy_seconds_left",
            "voting_seconds_left",
            "game_over",
            "finished",
            "done",
            "is_over",
        )
        return {k: game_state[k] for k in keys if k in game_state}

    def _ensure_memory_players(self, players: list[str]) -> None:
        for name in players:
            if name != self.config.agent_name:
                self.memory.ensure_agent(name)

    @staticmethod
    def _extract_messages(raw_messages: Any) -> list[dict[str, Any]]:
        if isinstance(raw_messages, list):
            return [m for m in raw_messages if isinstance(m, dict)]
        if isinstance(raw_messages, dict):
            if isinstance(raw_messages.get("messages"), list):
                return [m for m in raw_messages["messages"] if isinstance(m, dict)]
        return []

    def _apply_behavior_predictions(self, predictions: dict[str, str]) -> None:
        for name, note in predictions.items():
            if name in self.memory.opponent_profiles:
                profile = self.memory.opponent_profiles[name]
                profile.rationale = note[:180]

    def _handle_diplomacy(self, round_number: int, phase: str) -> None:
        raw_messages = self.client.get_messages()
        messages = self._extract_messages(raw_messages)
        for msg in messages:
            sender = str(msg.get("from") or msg.get("sender") or "")
            if sender and sender != self.config.agent_name:
                self.memory.ensure_agent(sender)

        profiles = self.opponent_modeler.update_profiles(self.memory, phase=phase)
        trust_rows = [
            {
                "agent": name,
                "trust_score": stats.trust_score,
                "cooperation_rate": stats.cooperation_rate,
                "betrayal_count": stats.betrayal_count,
                "profile": profiles.get(name).label if profiles.get(name) else "unknown",
            }
            for name, stats in sorted(self.memory.agents.items())
        ]
        candidates = [name for name in self.memory.agents.keys() if name != self.config.agent_name]
        latest_leaderboard = self._latest_leaderboard()

        plan, llm_meta = self.llm_strategy.plan_diplomacy(
            me=self.config.agent_name,
            round_number=round_number,
            phase=phase,
            incoming_messages=messages,
            trust_rows=trust_rows,
            candidates=candidates,
            leaderboard_rows=latest_leaderboard,
        )
        self.logger.info(
            "LLM diplomacy plan using %s/%s fallback=%s targets=%s",
            llm_meta.provider,
            llm_meta.model,
            llm_meta.fallback_used,
            plan.ranked_targets[:3],
        )

        self._apply_behavior_predictions(plan.behavior_predictions)

        max_direct = self.config.max_direct_messages_per_diplomacy
        if 0 < round_number <= self.config.fast_start_rounds:
            max_direct += self.config.fast_start_extra_direct_messages
        max_direct = min(10, max_direct)

        sent = 0
        for target, message in plan.direct_messages:
            if target == self.config.agent_name:
                continue
            if target not in self.memory.agents:
                continue
            if sent >= max_direct:
                break
            self.client.send_message(target, message)
            self.memory.note_commitment(target)
            sent += 1

        if plan.broadcast_message:
            self.client.broadcast(plan.broadcast_message)

    def _handle_voting(self, round_number: int, phase: str) -> None:
        self.opponent_modeler.update_profiles(self.memory, phase=phase)
        candidates = [name for name in self.memory.agents.keys() if name != self.config.agent_name]
        option_scores = self.simulator.rank_options(self.memory, candidates)
        decision = self.rule_engine.finalize_vote(self.memory, option_scores)
        target = decision.target
        if not target:
            if candidates:
                target = candidates[0]
            elif option_scores and option_scores[0].target:
                target = option_scores[0].target
        self.client.submit_votes(target)
        self.memory.last_vote_target = target
        self.logger.info(
            "Vote decision -> target=%s ev=%.2f source=%s reason=%s",
            target if target else "abstain",
            decision.expected_value,
            decision.source,
            decision.reason,
        )

    def _update_after_round(self, finished_round_number: int) -> None:
        if finished_round_number <= 0 or finished_round_number in self.rounds_updated:
            return
        round_results = self.client.get_round_results(finished_round_number)
        alliances = self.client.get_alliances()
        leaderboard = self._normalize_leaderboard(self.client.get_leaderboard())
        self.memory.update_after_round(
            round_number=finished_round_number,
            round_results=round_results,
            alliances=alliances,
            leaderboard=leaderboard,
        )
        self.memory.save()
        self.rounds_updated.add(finished_round_number)
        self.logger.info("Round %s post-processing complete.", finished_round_number)

    @staticmethod
    def _normalize_leaderboard(raw: Any) -> list[dict[str, Any]]:
        if isinstance(raw, dict):
            nested = raw.get("leaderboard")
            if isinstance(nested, list):
                raw = nested
            else:
                return []
        if not isinstance(raw, list):
            return []
        normalized: list[dict[str, Any]] = []
        for item in raw:
            if not isinstance(item, dict):
                continue
            name = item.get("name")
            score = item.get("score")
            if not isinstance(name, str):
                continue
            try:
                score_num = float(score)
            except (TypeError, ValueError):
                score_num = 0.0
            normalized.append(
                {
                    "rank": int(item.get("rank", len(normalized) + 1)),
                    "name": name,
                    "score": score_num,
                }
            )
        normalized.sort(key=lambda row: row.get("score", 0.0), reverse=True)
        for i, row in enumerate(normalized):
            row["rank"] = i + 1
        return normalized

    def _latest_leaderboard(self) -> list[dict[str, Any]]:
        for record in reversed(self.memory.round_records):
            if record.leaderboard:
                return self._normalize_leaderboard(record.leaderboard)
        return []

    def run(self) -> None:
        try:
            reg_result = self.client.register(self.config.agent_name)
            self.logger.info("Register result: %s", reg_result)
        except MCPClientError as exc:
            self.logger.warning("Register warning: %s", exc)

        while True:
            try:
                game_state = self.client.get_game_state()
            except MCPClientError as exc:
                self.logger.warning("get_game_state failed: %s", exc)
                time.sleep(self.config.poll_interval_seconds)
                continue

            round_number = self._parse_round(game_state)
            phase = self._parse_phase(game_state)
            status = self._parse_status(game_state)
            game_over = self._parse_game_over(game_state)
            players = self._extract_players(game_state)

            self.memory.current_round = round_number
            self.memory.current_phase = phase
            self._ensure_memory_players(players)
            self._tick_counter += 1

            if self._tick_counter % self.config.log_game_state_every_ticks == 0:
                self.logger.info(
                    "State monitor -> status=%s round=%s phase=%s players_count=%s summary=%s",
                    status,
                    round_number,
                    phase,
                    len(players),
                    self._state_summary(game_state),
                )
                if self.config.log_game_state_payload:
                    self.logger.info("State payload -> %s", game_state)

            if game_over or round_number > self.config.max_rounds:
                final_round = 0
                if round_number > self.config.max_rounds:
                    final_round = self.config.max_rounds
                elif round_number > 0:
                    final_round = round_number
                if final_round > 0 and final_round not in self.rounds_updated:
                    try:
                        self._update_after_round(final_round)
                    except MCPClientError as exc:
                        self.logger.warning(
                            "Final round %s sync failed before shutdown: %s",
                            final_round,
                            exc,
                        )
                self.logger.info("Game ended or max rounds exceeded. Stopping.")
                break

            if status in {"setup", "lobby"}:
                time.sleep(self.config.poll_interval_seconds)
                continue

            if phase.startswith("diplomacy"):
                key = (round_number, "diplomacy")
                if key not in self.executed_phase_actions:
                    self._handle_diplomacy(round_number, phase)
                    self.executed_phase_actions.add(key)
            elif phase.startswith("voting"):
                key = (round_number, "voting")
                if key not in self.executed_phase_actions:
                    self._handle_voting(round_number, phase)
                    self.executed_phase_actions.add(key)

            if phase in {"results", "summary", "round_end"}:
                self._update_after_round(round_number)
            elif round_number > 1 and (round_number - 1) not in self.rounds_updated:
                self._update_after_round(round_number - 1)

            time.sleep(self.config.poll_interval_seconds)

        self.memory.save()
        self.router.close()
        self.client.close()
