import asyncio
import io
import json
import os
from typing import Any, Dict, List

import httpx
from applicant_tools import ApplicantTool
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client
from models import EvaluationList, JobPostingList, NotificationList, State
from pypdf import PdfReader


class ApplicantAgent:
    """Agents that are used during the job application process"""

    def __init__(
        self,
        username: str,
        no_of_postings: int,
        model: str = "gpt-4o-mini",
        google_drive_file_id: str | None = None,
    ):
        self.username = username
        self.no_of_postings = no_of_postings
        self.tool: ApplicantTool = None
        self.playwright_tools = None
        self.other_tools = None
        self.browser = None
        self.playwright = None
        self.file_tools = None
        self.search_tool = None
        self.send_email_tool = None
        self.send_push_notification_tool = None
        self.model: str = model
        self.llm: ChatOpenAI = None
        self.user_profile_summary: str = None
        self.google_drive_file_id = google_drive_file_id or os.getenv(
            "PROFILE_GOOGLE_DRIVE_FILE_ID"
        )
        self.smithery_api_key = os.getenv("SMITHERY_API_KEY")
        self.googledrive_mcp_endpoint = os.getenv("GOOGLEDRIVE_MCP_ENDPOINT")

    async def setup(self):
        """
        Setup the applicant agent
        """
        self.tool = ApplicantTool()
        (
            self.playwright_tools,
            self.browser,
            self.playwright,
        ) = await self.tool.playwright_tools()
        self.other_tools = await self.tool.get_other_tools()
        self.file_tools = self.other_tools["file"]
        self.search_tool = self.other_tools["search"]
        self.email_tool = self.other_tools["email"]
        self.push_notification_tool = self.other_tools["push_notification"]
        self.llm = ChatOpenAI(model=self.model)
        await self.get_user_profile_summary()

    async def get_user_profile_summary(self) -> None:
        """
        Get the user profile summary
        """
        pdf_bytes = await self._download_from_google_drive()
        reader = PdfReader(io.BytesIO(pdf_bytes))
        user_profile = "\n\n".join(page.extract_text() for page in reader.pages)
        user_profile_summary_instructions = f"""
        You are a user profile summary assistant helping {self.username} get their profile summary.

        ## Objective
        Given the user's profile, you will extract the profile summary and a concise summary of the user's profile and skills.

        ## Requirements
        - Extract a concise summary of the user's profile and skills.
        - The summary should be a concise summary of the user's profile and skills.
        - The summary should be no more than 500 words.

        The user's profile: {user_profile}
        """
        user_profile_summary_message = (
            f"Get the user profile summary for {self.username}"
        )
        messages = [
            SystemMessage(content=user_profile_summary_instructions),
            HumanMessage(content=user_profile_summary_message),
        ]
        response = await self.llm.ainvoke(input=messages)
        self.user_profile_summary = response.content

    async def _download_from_google_drive(self) -> bytes:
        """Download a file from Google Drive using the Smithery MCP server."""

        def client_factory(**kwargs):
            existing_headers = kwargs.pop("headers", {})
            return httpx.AsyncClient(
                headers={
                    **existing_headers,
                    "Authorization": f"Bearer {self.smithery_api_key}",
                    "Accept": "application/json, text/event-stream",
                },
                **kwargs,
            )

        async with streamablehttp_client(
            self.googledrive_mcp_endpoint,
            httpx_client_factory=client_factory,
        ) as (read, write, _):
            async with ClientSession(read, write) as session:
                await session.initialize()
                result = await session.call_tool(
                    "download_file",
                    {"file_id": self.google_drive_file_id},
                )
                response = json.loads(result.content[0].text)
                s3_url = response["downloaded_file_content"]["s3url"]

                async with httpx.AsyncClient() as client:
                    file_response = await client.get(s3_url)
                    file_response.raise_for_status()
                    return file_response.content

    async def listing_worker(self, state: State) -> Dict[str, JobPostingList]:
        """
        Listing worker
        """
        job_posting_url = state.job_posting_url
        listing_instructions = f"""
            You are a job listing assistant helping {self.username} find relevant job opportunities.

            ## Objective
            Given the job posting url, you will extract the job posting details and return them in a structured format.
            Use the provded tools to fetch the job posting details.

            ## Requirements
            - Return EXACTLY {self.no_of_postings} job postings.
            - Prioritize recency (most recent postings first).
            - Ensure jobs are relevant to the {self.username}'s profile.

            User profile summary: {self.user_profile_summary}

            ## Data Quality Rules
            For each job posting:
            - title: Clear and accurate job title.
            - company_name: Company name only.
            - company_url: Valid company page URL (if available).
            - location: City/Country or "Remote" if applicable.
            - salary_range: Extract if available, otherwise "Not specified".
            - job_description: Concise summary (3-5 sentences, not full copy).
            - job_requirements: Key responsibilities (bullet-style but as text).
            - technologies_needed: Extract explicit tools/tech (e.g. Python, React, AWS).
            - must_have_skills: Core required skills only (not nice-to-haves).
            - link_to_job_posting: Direct job URL (must be valid).
            - job_posting_date: Relative or exact (e.g. "2 days ago" or "2026-03-10").

            ## Constraints
            - Do NOT hallucinate links or companies.
            - If data is missing, use "Not specified".
            - Avoid duplication.
            - Keep descriptions concise and structured.

            ## Output
            - Return ONLY structured data matching JobPostingList schema.
            - No explanations, no extra text.
            - Return exactly {self.no_of_postings} job postings.
            """
        listing_message = (
            f"Fetch job postings from LinkedIn using the link: {job_posting_url}"
        )
        listing_tools = [self.search_tool]
        llm_with_tools = self.llm.bind_tools(listing_tools).with_structured_output(
            JobPostingList
        )
        messages = [
            SystemMessage(content=listing_instructions),
            HumanMessage(content=listing_message),
        ]
        response = await llm_with_tools.ainvoke(input=messages)
        return {"job_postings": response}

    async def evaluate_job_postings(self, state: State) -> Dict[str, EvaluationList]:
        """
        Evaluate the job postings
        """
        job_postings = state.job_postings
        evaluator_instructions = f"""
                You are a Job Fit Evaluation Agent.

                ## Objective
                Given a job posting link, determine whether the role is a strong fit for {self.username} based on their experience, skills, and tech stack.
                Use the provided tools to get the job posting details.

                ## Required Actions
                - Analyze the job postings using the provided user profile summary and the job posting details.
                - Extract key responsibilities, required skills, and technologies from the provided link.

                ## Evaluation Criteria

                ### 1. Skills Match
                - Do the required skills align with {self.username}'s actual experience?
                - Focus on MUST-HAVE skills, not nice-to-haves.

                ### 2. Tech Stack Alignment
                - Compare required technologies with {self.username}'s known stack.
                - Strong match = majority overlap.

                ### 3. Experience Level
                - Is the role seniority appropriate (junior/mid/senior)?

                ### 4. Domain Relevance
                - Is the role aligned with {self.username}'s focus (e.g. software engineering, ML infrastructure, frontend, etc.)?

                ## Decision Rules
                - `is_acceptable = true` ONLY if:
                - There is a strong overlap in core skills AND tech stack
                - AND the role is at an appropriate experience level
                - Otherwise, `is_acceptable = false`

                ## Feedback Guidelines
                - Be concise and specific.
                - Highlight:
                - Matching strengths
                - Missing critical skills (if any)
                - Overall fit reasoning

                ## Constraints
                - Do NOT hallucinate user skills.
                - Base decisions strictly on retrieved profile + summary.
                - If job details are unclear or insufficient, mark as not acceptable.

                ## Output
                Return ONLY:
                - is_acceptable (boolean)
                - feedback (clear, actionable reasoning)
                - job_posting_id (str) the actual id of the job posting
                """
        evaluator_message = f"""
        Evaluate the following job postings: 
        {job_postings}
        
        given my profile summary: {self.user_profile_summary}"""

        evaluator_tools = self.playwright_tools
        llm_with_tools = self.llm.bind_tools(evaluator_tools).with_structured_output(
            EvaluationList
        )
        messages = [
            SystemMessage(content=evaluator_instructions),
            HumanMessage(content=evaluator_message),
        ]
        response = await llm_with_tools.ainvoke(input=messages)
        return {"evaluations": response}

    async def notification_worker(self, state: State) -> Dict[str, List[Any]]:
        """
        Notify the user of the job postings that are acceptable
        """
        evaluations: EvaluationList = state.evaluations
        job_postings: JobPostingList = state.job_postings
        notification_instructions = f"""
        You are a notification assistant helping {self.username} get notified of the job postings that are acceptable.

        Use the evaluations to get the evaluations of the job postings that are acceptable.
        Acceptable job postings are the job postings that have is_acceptable = true.
        use the feedback to get the feedback of the job postings that are acceptable.
        use the job_posting_id to get the id of the job postings that are acceptable.

        After getting the details of the acceptable job postings, notify the user of the job postings that are acceptable.
        use the provided tools to notify the user of the job postings that are acceptable.

        For each acceptable job posting, notify the user of the job posting details and the feedback.
        Make sure that you send them as a list with the job posting details and the feedback.

        After notifying the user, return the notifications as a list of notifications.
        """
        notification_message = f"""
        Notify the user of the job postings that are acceptable: 
        evaluated postings are:{evaluations}
        job postings are: {job_postings}
        """
        notification_tools = [self.push_notification_tool]
        llm_with_tools = self.llm.bind_tools(notification_tools).with_structured_output(
            NotificationList
        )
        messages = [
            SystemMessage(content=notification_instructions),
            HumanMessage(content=notification_message),
        ]
        response = await llm_with_tools.ainvoke(input=messages)
        return {"notifications": response}

    async def notification_response(self, state: State) -> Dict[str, List[Any]]:
        """
        Notification response
        """
        notifications: NotificationList = state.notifications
        notification_response_instructions = f"""
        You are a notification response assistant helping {self.username} get the response of the notifications.

        Use markdown to format the notification list into a readable format.
        """
        notification_response_message = f"""
        Notify the user of the job postings that are acceptable: 
        notifications are: {notifications}
        """
        messages = [
            SystemMessage(content=notification_response_instructions),
            HumanMessage(content=notification_response_message),
        ]
        response = await self.llm.ainvoke(input=messages)
        return {"messages": [response]}

    def cleanup(self):
        if self.browser:
            try:
                loop = asyncio.get_running_loop()
                loop.create_task(self.browser.close())
                if self.playwright:
                    loop.create_task(self.playwright.stop())
            except RuntimeError:
                # If no loop is running, do a direct run
                asyncio.run(self.browser.close())
                if self.playwright:
                    asyncio.run(self.playwright.stop())
