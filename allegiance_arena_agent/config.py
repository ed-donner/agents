from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv


@dataclass(slots=True)
class ModelSpec:
    provider: str
    model: str


@dataclass(slots=True)
class ArenaConfig:
    agent_name: str
    endpoint: str = "https://alliance.abdull.dev/mcp"
    poll_interval_seconds: float = 1.0
    max_rounds: int = 10
    memory_path: str = "allegiance_arena_agent/state.json"
    log_level: str = "INFO"
    log_game_state_every_ticks: int = 5
    log_game_state_payload: bool = False

    # Core deterministic control knobs
    trust_decay: float = 0.92
    abstain_threshold: float = -0.1
    max_direct_messages_per_diplomacy: int = 3
    fast_start_rounds: int = 3
    fast_start_extra_direct_messages: int = 2
    simulation_runs: int = 60
    simulation_enabled_monte_carlo: bool = True
    risk_penalty_weight: float = 0.55
    avoid_leader_when_behind: bool = True
    leader_gap_activation: float = 8.0
    leader_target_penalty_weight: float = 0.9
    catchup_min_ev: float = 0.35
    catchup_ev_delta_max: float = 0.6
    isolation_support_bonus_weight: float = 1.1
    profile_confidence_floor: float = 0.3
    min_primary_pacts: int = 2
    min_backup_pacts: int = 1

    # MCP networking
    mcp_timeout_seconds: float = 8.0
    mcp_max_retries: int = 3
    mcp_retry_backoff_seconds: float = 0.5

    # LLM credentials
    groq_api_key: str | None = None
    anthropic_api_key: str | None = None
    openrouter_api_key: str | None = None
    openrouter_site_url: str | None = None
    openrouter_app_name: str = "allegiance-arena-agent"

    # Flexible timeout profiles (seconds)
    base_timeouts: dict[str, float] = field(
        default_factory=lambda: {
            "strategy_planning": 5.0,
            "opponent_modeling": 5.5,
            "messaging": 3.5,
            "fallback_strategy": 3.0,
            "realtime_backup_messaging": 1.8,
        }
    )
    phase_timeout_multiplier: dict[str, float] = field(
        default_factory=lambda: {
            "setup": 1.2,
            "lobby": 1.2,
            "diplomacy": 1.0,
            "voting": 0.9,
            "results": 1.1,
            "unknown": 1.0,
        }
    )

    # Model routing (user-selected defaults)
    strategy_primary: ModelSpec = field(
        default_factory=lambda: ModelSpec(provider="groq", model="llama-3.1-8b-instant")
    )
    strategy_backup: ModelSpec = field(
        default_factory=lambda: ModelSpec(provider="openrouter", model="gpt-4o-mini")
    )
    opponent_primary: ModelSpec = field(
        default_factory=lambda: ModelSpec(provider="groq", model="openai/gpt-oss-20b")
    )
    opponent_backup: ModelSpec = field(
        default_factory=lambda: ModelSpec(provider="groq", model="llama-3.1-8b-instant")
    )
    messaging_primary: ModelSpec = field(
        default_factory=lambda: ModelSpec(provider="groq", model="mistral-7b-instruct")
    )
    messaging_backup: ModelSpec = field(
        default_factory=lambda: ModelSpec(provider="openrouter", model="gpt-4o-mini")
    )
    realtime_backup_messaging: ModelSpec = field(
        default_factory=lambda: ModelSpec(provider="groq", model="gemma-2-2b")
    )
    fallback_strategy_brain: ModelSpec = field(
        default_factory=lambda: ModelSpec(provider="openrouter", model="gpt-4o-mini")
    )

    @classmethod
    def from_env(cls, env_path: str | None = None) -> "ArenaConfig":
        if env_path:
            load_dotenv(env_path)
        else:
            default_env = Path(__file__).resolve().parent / ".env"
            if default_env.exists():
                load_dotenv(default_env)
            load_dotenv()

        agent_name = os.getenv("ARENA_AGENT_NAME", "").strip()
        if not agent_name:
            raise ValueError("ARENA_AGENT_NAME is required.")
        defaults = cls(agent_name=agent_name)

        def _model(prefix: str, fallback: ModelSpec) -> ModelSpec:
            provider = os.getenv(f"{prefix}_PROVIDER", fallback.provider).strip().lower()
            model = os.getenv(f"{prefix}_MODEL", fallback.model).strip()
            return ModelSpec(provider=provider, model=model)

        return cls(
            agent_name=agent_name,
            endpoint=os.getenv("ARENA_ENDPOINT", defaults.endpoint),
            poll_interval_seconds=float(
                os.getenv("ARENA_POLL_INTERVAL_SECONDS", defaults.poll_interval_seconds)
            ),
            max_rounds=int(os.getenv("ARENA_MAX_ROUNDS", defaults.max_rounds)),
            memory_path=os.getenv("ARENA_MEMORY_PATH", defaults.memory_path),
            log_level=os.getenv("ARENA_LOG_LEVEL", defaults.log_level),
            log_game_state_every_ticks=max(
                1,
                int(
                    os.getenv(
                        "ARENA_LOG_GAME_STATE_EVERY_TICKS",
                        defaults.log_game_state_every_ticks,
                    )
                ),
            ),
            log_game_state_payload=(
                os.getenv("ARENA_LOG_GAME_STATE_PAYLOAD", "false").lower()
                in {"1", "true", "yes", "on"}
            ),
            trust_decay=float(os.getenv("ARENA_TRUST_DECAY", defaults.trust_decay)),
            abstain_threshold=float(
                os.getenv("ARENA_ABSTAIN_THRESHOLD", defaults.abstain_threshold)
            ),
            max_direct_messages_per_diplomacy=int(
                os.getenv(
                    "ARENA_MAX_DIRECT_MESSAGES_PER_DIPLOMACY",
                    defaults.max_direct_messages_per_diplomacy,
                )
            ),
            fast_start_rounds=max(
                0,
                int(os.getenv("ARENA_FAST_START_ROUNDS", defaults.fast_start_rounds)),
            ),
            fast_start_extra_direct_messages=max(
                0,
                int(
                    os.getenv(
                        "ARENA_FAST_START_EXTRA_DIRECT_MESSAGES",
                        defaults.fast_start_extra_direct_messages,
                    )
                ),
            ),
            simulation_runs=int(os.getenv("ARENA_SIMULATION_RUNS", defaults.simulation_runs)),
            simulation_enabled_monte_carlo=(
                os.getenv(
                    "ARENA_SIMULATION_MONTE_CARLO",
                    "true" if defaults.simulation_enabled_monte_carlo else "false",
                ).lower()
                in {"1", "true", "yes", "on"}
            ),
            risk_penalty_weight=float(
                os.getenv("ARENA_RISK_PENALTY_WEIGHT", defaults.risk_penalty_weight)
            ),
            avoid_leader_when_behind=(
                os.getenv(
                    "ARENA_AVOID_LEADER_WHEN_BEHIND",
                    "true" if defaults.avoid_leader_when_behind else "false",
                ).lower()
                in {"1", "true", "yes", "on"}
            ),
            leader_gap_activation=float(
                os.getenv("ARENA_LEADER_GAP_ACTIVATION", defaults.leader_gap_activation)
            ),
            leader_target_penalty_weight=float(
                os.getenv(
                    "ARENA_LEADER_TARGET_PENALTY_WEIGHT",
                    defaults.leader_target_penalty_weight,
                )
            ),
            catchup_min_ev=float(
                os.getenv("ARENA_CATCHUP_MIN_EV", defaults.catchup_min_ev)
            ),
            catchup_ev_delta_max=float(
                os.getenv("ARENA_CATCHUP_EV_DELTA_MAX", defaults.catchup_ev_delta_max)
            ),
            isolation_support_bonus_weight=float(
                os.getenv(
                    "ARENA_ISOLATION_SUPPORT_BONUS_WEIGHT",
                    defaults.isolation_support_bonus_weight,
                )
            ),
            profile_confidence_floor=float(
                os.getenv(
                    "ARENA_PROFILE_CONFIDENCE_FLOOR",
                    defaults.profile_confidence_floor,
                )
            ),
            min_primary_pacts=max(
                1,
                int(os.getenv("ARENA_MIN_PRIMARY_PACTS", defaults.min_primary_pacts)),
            ),
            min_backup_pacts=max(
                0,
                int(os.getenv("ARENA_MIN_BACKUP_PACTS", defaults.min_backup_pacts)),
            ),
            mcp_timeout_seconds=float(
                os.getenv("ARENA_MCP_TIMEOUT_SECONDS", defaults.mcp_timeout_seconds)
            ),
            mcp_max_retries=int(os.getenv("ARENA_MCP_MAX_RETRIES", defaults.mcp_max_retries)),
            mcp_retry_backoff_seconds=float(
                os.getenv(
                    "ARENA_MCP_RETRY_BACKOFF_SECONDS",
                    defaults.mcp_retry_backoff_seconds,
                )
            ),
            groq_api_key=os.getenv("GROQ_API_KEY") or os.getenv("ARENA_GROQ_API_KEY"),
            anthropic_api_key=os.getenv("ANTHROPIC_API_KEY")
            or os.getenv("ARENA_ANTHROPIC_API_KEY"),
            openrouter_api_key=os.getenv("OPENROUTER_API_KEY")
            or os.getenv("ARENA_OPENROUTER_API_KEY"),
            openrouter_site_url=os.getenv("OPENROUTER_SITE_URL")
            or os.getenv("ARENA_OPENROUTER_SITE_URL"),
            openrouter_app_name=os.getenv(
                "OPENROUTER_APP_NAME", defaults.openrouter_app_name
            ),
            base_timeouts={
                "strategy_planning": float(
                    os.getenv(
                        "ARENA_TIMEOUT_STRATEGY_SECONDS",
                        defaults.base_timeouts["strategy_planning"],
                    )
                ),
                "opponent_modeling": float(
                    os.getenv(
                        "ARENA_TIMEOUT_OPPONENT_SECONDS",
                        defaults.base_timeouts["opponent_modeling"],
                    )
                ),
                "messaging": float(
                    os.getenv(
                        "ARENA_TIMEOUT_MESSAGING_SECONDS",
                        defaults.base_timeouts["messaging"],
                    )
                ),
                "fallback_strategy": float(
                    os.getenv(
                        "ARENA_TIMEOUT_FALLBACK_STRATEGY_SECONDS",
                        defaults.base_timeouts["fallback_strategy"],
                    )
                ),
                "realtime_backup_messaging": float(
                    os.getenv(
                        "ARENA_TIMEOUT_REALTIME_BACKUP_SECONDS",
                        defaults.base_timeouts["realtime_backup_messaging"],
                    )
                ),
            },
            phase_timeout_multiplier={
                "setup": float(
                    os.getenv(
                        "ARENA_TIMEOUT_MULTIPLIER_SETUP",
                        defaults.phase_timeout_multiplier["setup"],
                    )
                ),
                "lobby": float(
                    os.getenv(
                        "ARENA_TIMEOUT_MULTIPLIER_LOBBY",
                        defaults.phase_timeout_multiplier["lobby"],
                    )
                ),
                "diplomacy": float(
                    os.getenv(
                        "ARENA_TIMEOUT_MULTIPLIER_DIPLOMACY",
                        defaults.phase_timeout_multiplier["diplomacy"],
                    )
                ),
                "voting": float(
                    os.getenv(
                        "ARENA_TIMEOUT_MULTIPLIER_VOTING",
                        defaults.phase_timeout_multiplier["voting"],
                    )
                ),
                "results": float(
                    os.getenv(
                        "ARENA_TIMEOUT_MULTIPLIER_RESULTS",
                        defaults.phase_timeout_multiplier["results"],
                    )
                ),
                "unknown": float(
                    os.getenv(
                        "ARENA_TIMEOUT_MULTIPLIER_UNKNOWN",
                        defaults.phase_timeout_multiplier["unknown"],
                    )
                ),
            },
            strategy_primary=_model("ARENA_MODEL_STRATEGY_PRIMARY", defaults.strategy_primary),
            strategy_backup=_model("ARENA_MODEL_STRATEGY_BACKUP", defaults.strategy_backup),
            opponent_primary=_model("ARENA_MODEL_OPPONENT_PRIMARY", defaults.opponent_primary),
            opponent_backup=_model("ARENA_MODEL_OPPONENT_BACKUP", defaults.opponent_backup),
            messaging_primary=_model("ARENA_MODEL_MESSAGING_PRIMARY", defaults.messaging_primary),
            messaging_backup=_model("ARENA_MODEL_MESSAGING_BACKUP", defaults.messaging_backup),
            realtime_backup_messaging=_model(
                "ARENA_MODEL_REALTIME_BACKUP", defaults.realtime_backup_messaging
            ),
            fallback_strategy_brain=_model(
                "ARENA_MODEL_FALLBACK_STRATEGY", defaults.fallback_strategy_brain
            ),
        )

    def timeout_for(self, component: str, phase: str) -> float:
        base = self.base_timeouts.get(component, 4.0)
        multiplier = self.phase_timeout_multiplier.get(phase.lower(), 1.0)
        return max(0.5, base * multiplier)
