"""
Orchestrator: runs the scholarship research pipeline using state (LangGraph-style).
Flow: create agents -> researcher -> evaluator -> complete.
"""

import asyncio
import logging
from typing import Optional

from autogen_core import SingleThreadedAgentRuntime, AgentId

from . import messages
from .states import ScholarshipResearchState, Phase
from .tools import get_serper_tool, get_playwright_tools
from .creator import Creator

logger = logging.getLogger(__name__)

DEFAULT_RESEARCH_REQUEST = (
    "Find and list universities in Australia that are currently offering scholarships. "
    "Include scholarship name, university, key details (amount/eligibility/deadline where available), "
    "and source URL. Use web search and browser to verify official pages."
)

DEFAULT_EVALUATION_PROMPT = (
    "Evaluate the following research findings about Australian university scholarships. "
    "Check: (1) Is the information correct and scholarship-related? "
    "(2) Are university names, program names, and key details present and plausible? "
    "Use your tools to spot-check if needed. Respond with your verdict and a short summary."
)


async def run_pipeline(
    research_request: Optional[str] = None,
    evaluation_prompt: Optional[str] = None,
) -> ScholarshipResearchState:
    """
    Run the full pipeline: create agents via Creator, then researcher -> evaluator.
    Uses ScholarshipResearchState to pass data between steps (LangGraph-style).
    """
    state = ScholarshipResearchState(
        research_request=research_request or DEFAULT_RESEARCH_REQUEST,
        current_phase=Phase.INIT,
    )
    evaluation_prompt = evaluation_prompt or DEFAULT_EVALUATION_PROMPT

    # Build shared tools (Serper + Playwright)
    serper = get_serper_tool()
    playwright_adapters, browser, playwright = await get_playwright_tools()
    all_tools = [serper] + playwright_adapters

    runtime = SingleThreadedAgentRuntime()
    await Creator.register(
        runtime,
        "Creator",
        lambda: Creator("Creator", tools=all_tools),
    )
    runtime.start()

    try:
        creator_id = AgentId("Creator", "default")

        # Step 1: Ask Creator to create Researcher and Evaluator
        state.current_phase = Phase.RESEARCH_REQUESTED
        create_msg = messages.Message(content="create_scholarship_team")
        create_result = await runtime.send_message(create_msg, creator_id)
        state.metadata["creator_response"] = create_result.content
        logger.info("Creator response: %s", create_result.content[:200] if create_result.content else "")

        # Step 2: Send research task to Researcher
        state.current_phase = Phase.RESEARCHER_RUNNING
        research_msg = messages.Message(content=state.research_request)
        researcher_id = AgentId("Researcher", "default")
        researcher_response = await runtime.send_message(research_msg, researcher_id)
        state.researcher_findings = researcher_response.content
        state.current_phase = Phase.RESEARCHER_DONE
        logger.info("Researcher completed.")

        # Step 3: Send findings to Evaluator
        state.current_phase = Phase.EVALUATOR_RUNNING
        eval_content = f"{evaluation_prompt}\n\n--- RESEARCH FINDINGS ---\n{state.researcher_findings}"
        eval_msg = messages.Message(content=eval_content)
        evaluator_id = AgentId("Evaluator", "default")
        evaluator_response = await runtime.send_message(eval_msg, evaluator_id)
        state.evaluator_verdict = evaluator_response.content
        state.current_phase = Phase.COMPLETE
        logger.info("Evaluator completed. Pipeline done.")

    except Exception as e:
        state.current_phase = Phase.ERROR
        state.error = str(e)
        logger.exception("Pipeline error")
    finally:
        await runtime.stop()
        await runtime.close()
        if browser:
            await browser.close()
        if playwright:
            await playwright.stop()

    return state
