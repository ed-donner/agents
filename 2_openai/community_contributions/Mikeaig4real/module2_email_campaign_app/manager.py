"""Execution manager for module 2 email campaign app."""

from agents import Runner, gen_trace_id, trace
from lead_agent import sales_manager


class EmailCampaignManager:
    """Runs the converged campaign manager agent."""

    async def run(self, prompt: str):
        """Stream trace link and final campaign output."""
        trace_id = gen_trace_id()
        with trace("module2_email_campaign", trace_id=trace_id):
            yield f"Trace link (requires valid dashboard access): https://platform.openai.com/traces/trace?trace_id={trace_id}"
            yield "Running sales manager..."
            result = await Runner.run(sales_manager, prompt)
            yield str(result.final_output)
