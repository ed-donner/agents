from crewai.tools import BaseTool
from typing import Type
from pydantic import BaseModel, Field
import requests


class InvestorFinderInput(BaseModel):
    startup_niche: str = Field(..., description="The niche or industry of the startup")


class InvestorFinderTool(BaseTool):
    name: str = "Investor Finder Tool"
    description: str = (
        "Finds potential investors interested in a specific startup niche."
    )
    args_schema: Type[BaseModel] = InvestorFinderInput

    def _run(self, startup_niche: str) -> str:
        # Example investors (you can later connect Crunchbase API or other sources)
        investors = [
            {"name": "Philip Onuchukwu", "email": "onuchukwus.philip@gmail.com"},
            {"name": "Sir Phil", "email": "sirphil.bizz@gmail.com"},
            {"name": "Philip Techpaxe", "email": "philip.techpaxe@gmail.com"}
        ]

        results = []
        for investor in investors:
            results.append(
                f"{investor['name']} - {investor['email']} (interested in {startup_niche})"
            )

        return "\n".join(results)