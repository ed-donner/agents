import os
from pathlib import Path

import requests
from agents import Agent, function_tool
from agents.mcp import MCPServerSse
from applicant import Applicant
from dotenv import load_dotenv
from pypdf import PdfReader
from templates import (
    evaluation_instructions,
    evaluation_tool,
    listing_instructions,
    listing_tool,
    manager_instructions,
    notification_instructions,
    notification_tool,
)

load_dotenv(override=True)


class ApplicantAgents:
    def __init__(self, name: str, model: str = "gpt-4o-mini"):
        self.name = name
        self.model = model
        self.applicant = Applicant.get(name)
        self.rapid_api_key = os.getenv("RAPID_API_KEY")
        self.rapid_api_host = os.getenv("RAPID_API_HOST")
        self.rapid_api_url = f"https://{self.rapid_api_host}/active-jb-7d"
        self.query_params = None
        if not self.applicant.summary:
            BASE_DIR = Path.cwd()
            profile_pdf_path = os.path.abspath(
                os.path.join(BASE_DIR, "sandbox", "linkedin.pdf")
            )
            with open(profile_pdf_path, "rb") as pdf_file:
                reader = PdfReader(pdf_file)
                profile = "\n".join([page.extract_text() for page in reader.pages])
            self.applicant.set_summary(profile)

    def _set_query_params(
        self,
        limit: int,
        advanced_title_filter: str,
        location_filter: str,
    ):
        self.query_params = {
            "limit": limit,
            "offset": 0,
            "advanced_title_filter": advanced_title_filter,
            "location_filter": location_filter,
            "description_type": "text",
        }

    def get_linkedin_results(
        self,
        limit: int = 10,
        advanced_title_filter: str = "AI Engineer | Software:*",
        location_filter: str = "Nairobi",
    ):
        # Bug fix: _set_query_params returns None; use self.query_params
        self._set_query_params(limit, advanced_title_filter, location_filter)
        headers = {
            "x-rapidapi-key": self.rapid_api_key,
            "x-rapidapi-host": self.rapid_api_host,
            "Content-Type": "application/json",
        }
        response = requests.get(
            self.rapid_api_url, headers=headers, params=self.query_params
        )
        return response.json()

    def _make_linkedin_tool(self):
        """
        Return a properly bound function_tool for get_linkedin_results.
        Cannot use @tool/@function_tool directly on a class method because
        the SDK would expose 'self' as a parameter for the LLM to fill.
        """
        get_results = self.get_linkedin_results

        @function_tool
        def get_linkedin_results(
            limit: int = 10,
            advanced_title_filter: str = "AI Engineer | Software:*",
            location_filter: str = "Nairobi",
        ):
            """Fetch LinkedIn job listings matching the given filters."""
            return get_results(limit, advanced_title_filter, location_filter)

        return get_linkedin_results

    async def get_listing_agent(self, applicant_server: MCPServerSse):
        listing_agent = Agent(
            name="listing_agent",
            instructions=listing_instructions(self.name),
            model=self.model,
            mcp_servers=[applicant_server],
            tools=[self._make_linkedin_tool()],
        )
        return listing_agent

    async def get_listing_agent_tool(self, applicant_server: MCPServerSse):
        listing_agent = await self.get_listing_agent(applicant_server)
        return listing_agent.as_tool(
            tool_name="get_linkedin_results",
            tool_description=listing_tool(),
        )

    async def get_evaluation_agent(self, applicant_server: MCPServerSse):
        listing_agent_tool = await self.get_listing_agent_tool(applicant_server)
        evaluation_agent = Agent(
            name="evaluation_agent",
            instructions=evaluation_instructions(self.name),
            model=self.model,
            mcp_servers=[applicant_server],
            tools=[listing_agent_tool],
        )
        return evaluation_agent

    async def get_evaluation_agent_tool(self, applicant_server: MCPServerSse):
        evaluation_agent = await self.get_evaluation_agent(applicant_server)
        return evaluation_agent.as_tool(
            tool_name="evaluate_job_post",
            tool_description=evaluation_tool(),
        )

    async def get_notification_agent(
        self, applicant_server: MCPServerSse, pdf_server: MCPServerSse
    ):
        evaluation_agent_tool = await self.get_evaluation_agent_tool(applicant_server)
        notification_agent = Agent(
            name="notification_agent",
            instructions=notification_instructions(self.name),
            model=self.model,
            mcp_servers=[applicant_server, pdf_server],
            tools=[evaluation_agent_tool],
        )
        return notification_agent

    async def get_notification_agent_tool(
        self, applicant_server: MCPServerSse, pdf_server: MCPServerSse
    ):
        notification_agent = await self.get_notification_agent(
            applicant_server, pdf_server
        )
        return notification_agent.as_tool(
            tool_name="send_job_application_email",
            tool_description=notification_tool(),
        )

    async def create_agent(
        self, applicant_server: MCPServerSse, pdf_server: MCPServerSse
    ):
        """
        Build and return the top-level manager agent.
        The manager has one tool: send_job_application_email (the notification agent),
        which in turn chains evaluation → listing internally.
        """
        notification_agent_tool = await self.get_notification_agent_tool(
            applicant_server, pdf_server
        )
        manager = Agent(
            name="manager_agent",
            instructions=manager_instructions(self.name),
            model=self.model,
            tools=[notification_agent_tool],
        )
        return manager
