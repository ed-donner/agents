from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

if __package__ in {None, ""}:
    parent = Path(__file__).resolve().parents[1]
    if str(parent) not in sys.path:
        sys.path.insert(0, str(parent))
    from allegiance_arena_agent.agent import CompetitiveArenaCoordinator
    from allegiance_arena_agent.config import ArenaConfig
else:
    from .agent import CompetitiveArenaCoordinator
    from .config import ArenaConfig


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run Allegiance Arena multi-agent system.")
    parser.add_argument("--env-file", default=None, help="Optional environment file path.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    config = ArenaConfig.from_env(env_path=args.env_file)

    logging.basicConfig(
        level=getattr(logging, config.log_level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s | %(message)s",
    )

    coordinator = CompetitiveArenaCoordinator(config)
    coordinator.run()


if __name__ == "__main__":
    main()
