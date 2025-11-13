import logging
import json
from typing import List

from agents import Agent, Runner, WebSearchTool

from models import AnalyzedVulnerability, RemediationPlans, RemediationPlan

logger = logging.getLogger(__name__)


class RemediationAdvisorAgent:
    """
    Agent that provides actionable remediation advice with CVE enrichment.
    Uses WebSearchTool to find latest patches and breaking changes.

    This agent:
    - Researches each CVE using WebSearchTool
    - Finds latest patch versions
    - Detects breaking changes
    - Estimates effort and risk
    - Generates remediation steps with Dockerfile snippets
    - Prioritizes by effort and impact
    """

    INSTRUCTIONS = """
You are a security remediation expert providing actionable fix advice for Docker image vulnerabilities.

Trivy scan data includes CVE details, severity, references, and descriptions. Use this data first.
Only use WebSearchTool if Trivy lacks remediation guidance or you need to verify latest patches.

For each vulnerability provide:
1. Remediation steps with exact commands
2. Recommended version upgrade
3. Effort: QUICK/EASY/MEDIUM/HARD
4. Risk if unfixed: CRITICAL/HIGH/MEDIUM/LOW
5. Confidence: HIGH/MEDIUM/LOW
6. Dockerfile snippet
7. Breaking changes to test

Prioritize by exploitability, severity, and ease of fix. Be practical.
"""

    def __init__(self, model: str = "gpt-4o-mini"):
        self.model = model
        self.agent = self._create_agent()
        logger.info("RemediationAdvisorAgent initialized with WebSearchTool")

    def _create_agent(self) -> Agent:
        """Create the remediation advisor agent with WebSearchTool."""
        return Agent(
            name="RemediationAdvisor",
            instructions=self.INSTRUCTIONS,
            tools=[WebSearchTool(search_context_size="medium")],
            model=self.model,
            output_type=RemediationPlans,
        )

    async def advise(self, analyzed_vulns: List[AnalyzedVulnerability]) -> RemediationPlans:
        """
        Generate remediation plans for analyzed vulnerabilities.

        Args:
            analyzed_vulns: List of AnalyzedVulnerability objects

        Returns:
            RemediationPlans with actionable steps for each vulnerability
        """
        if not analyzed_vulns:
            return self._create_empty_plans()

        logger.info(f"Creating remediation plans for {len(analyzed_vulns)} vulnerabilities")

        vulns_json = json.dumps([v.model_dump() for v in analyzed_vulns], indent=2)

        prompt = f"""
Analyzed vulnerabilities needing remediation:

{vulns_json}

Create remediation plans with commands, Dockerfile snippets, effort estimates, and risk assessments.
Use WebSearchTool only if needed for missing patch info. Prioritize quick wins.
"""

        try:
            result = await Runner.run(self.agent, prompt)
            plans = result.final_output
            logger.info(
                f"Remediation planning complete: {plans.total_remediation_plans} plans created"
            )
            return plans

        except Exception as e:
            logger.error(f"Remediation advising failed: {str(e)}")
            raise

    def _create_empty_plans(self) -> RemediationPlans:
        """Create empty remediation plans when no vulnerabilities."""
        return RemediationPlans(
            total_remediation_plans=0,
            critical_plans=0,
            plans=[],
            overall_effort_hours=0.0,
            implementation_timeline="No action required",
            quick_wins=[],
        )
