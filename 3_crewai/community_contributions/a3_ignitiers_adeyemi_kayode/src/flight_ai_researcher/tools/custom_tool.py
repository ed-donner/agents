from typing import Type

from crewai.tools import BaseTool
from pydantic import BaseModel, Field


class FlightAIResearchFrameworkInput(BaseModel):
    """Optional emphasis for the framework hints."""

    emphasis: str = Field(
        default="general",
        description='One of: "operations", "safety", "maintenance", "passenger", "general".',
    )


class FlightAIResearchFrameworkTool(BaseTool):
    name: str = "flight_ai_research_framework"
    description: str = (
        "Returns a concise checklist of aviation AI research subdomains (flight ops, "
        "MRO, ATC, safety, passenger experience) to scope or plan research before web search."
    )
    args_schema: Type[BaseModel] = FlightAIResearchFrameworkInput

    def _run(self, emphasis: str = "general") -> str:
        base = """
## Flight & agentic-AI research scaffolding (use to structure queries)

1. **Operations & dispatch** — AI copilots for dispatch, fuel/trajectory optimization, disruption recovery.
2. **Predictive maintenance & MRO** — PHM, digital twins, spare-parts forecasting, OEM analytics platforms.
3. **Crew & rostering** — fatigue models, pairing optimization, training simulators with AI scenarios.
4. **Air traffic & airspace** — trajectory-based ops, AI decision support for ATC (where permitted), UTM.
5. **Safety & certification** — assurance, human-AI teaming, SOTIF, regulatory expectations (EASA/FAA themes).
6. **Passenger & airport** — biometrics, chatbots, turnaround optimization, baggage/ramp AI.
7. **Agentic systems** — multi-agent workflows, tool-using agents for ops research, guardrails and audit trails.
"""
        focus = {
            "operations": "\n**Focus:** prioritize ops, dispatch, and network recovery.\n",
            "safety": "\n**Focus:** prioritize certification, assurance, human factors, incident prevention.\n",
            "maintenance": "\n**Focus:** prioritize MRO, PHM, supply chain, OEM digital threads.\n",
            "passenger": "\n**Focus:** prioritize airport, cabin, and customer-facing AI.\n",
            "general": "",
        }.get(emphasis.lower(), "")
        return base.strip() + focus
