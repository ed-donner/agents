"""
Entry point for the Australia Scholarship Research pipeline.
Runs: Creator (creates Researcher + Evaluator) -> Researcher -> Evaluator.
"""

import asyncio
import logging
import os

from dotenv import load_dotenv

# Load .env from repo root (agents/) when run from community_contributions
_load_dir = os.path.dirname(os.path.abspath(__file__))
for _ in range(4):
    _env = os.path.join(_load_dir, ".env")
    if os.path.isfile(_env):
        load_dotenv(_env, override=True)
        break
    _load_dir = os.path.dirname(_load_dir)
load_dotenv(override=True)

from .orchestrator import run_pipeline
from .states import Phase

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def main():
    logger.info("Starting Australia Scholarship Research pipeline (state-driven).")
    state = await run_pipeline()
    logger.info("Pipeline finished. Phase: %s", state.current_phase)
    if state.error:
        logger.error("Error: %s", state.error)
    if state.researcher_findings:
        print("\n--- RESEARCHER FINDINGS ---\n")
        print(state.researcher_findings[:4000] + ("..." if len(state.researcher_findings or "") > 4000 else ""))
    if state.evaluator_verdict:
        print("\n--- EVALUATOR VERDICT ---\n")
        print(state.evaluator_verdict[:3000] + ("..." if len(state.evaluator_verdict or "") > 3000 else ""))
    return state


if __name__ == "__main__":
    asyncio.run(main())
