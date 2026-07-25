import os
import smtplib
from pathlib import Path
from typing import Literal

from langchain_community.agent_toolkits import (
    FileManagementToolkit,
    PlayWrightBrowserToolkit,
)
from langchain_community.utilities import GoogleSerperAPIWrapper
from langchain_core.tools import Tool
from playwright.async_api import async_playwright
from requests import Response, post


class ApplicantTool:
    """Tools that are used during the job application process"""

    def __init__(self):
        self.from_email: str | None = os.getenv("FROM_EMAIL")
        self.email_host: str | None = os.getenv("EMAIL_HOST")
        self.email_port: int | None = os.getenv("EMAIL_PORT")
        self.google_app_password: str | None = os.getenv("GOOGLE_APP_PASSWORD")
        self.pushover_token: str | None = os.getenv("PUSHOVER_TOKEN")
        self.pushover_user: str | None = os.getenv("PUSHOVER_USER")
        self.pushover_url: str | None = os.getenv("PUSHOVER_URL")
        self.serper: GoogleSerperAPIWrapper = GoogleSerperAPIWrapper()
        self.output_dir: str = os.getenv("OUTPUT_DIR", "results")
        self.base_path: Path = str(Path(__file__).resolve().parent)

    def _send_push_notification(self, message: str) -> str:
        """Send a push notification to the user"""
        if not all([self.pushover_token, self.pushover_user, self.pushover_url]):
            raise ValueError(
                "Missing one or more required environment variables: PUSHOVER_TOKEN, PUSHOVER_USER, PUSHOVER_URL"
            )
        payload: dict[str, str] = {
            "user": self.pushover_user,
            "token": self.pushover_token,
            "message": message,
        }
        response: Response = post(self.pushover_url, data=payload)
        res: Literal[
            "Push notification sent successfully", "Failed to send push notification"
        ] = (
            "Push notification sent successfully"
            if response.status_code == 200
            else "Failed to send push notification"
        )
        return res

    def _send_email(
        self, subject: str, body: str, email_address: str
    ) -> Literal["Email sent successfully", "Failed to send email"]:
        """Send an email to the user"""
        if not all(
            [
                self.from_email,
                self.google_app_password,
                self.email_host,
                self.email_port,
            ]
        ):
            raise ValueError(
                "Missing one or more required environment variables: FROM_EMAIL, GOOGLE_APP_PASSWORD, EMAIL_HOST, EMAIL_PORT"
            )
        with smtplib.SMTP_SSL(self.email_host, self.email_port) as server:
            server.login(self.from_email, self.google_app_password)
            response = server.sendmail(self.from_email, email_address, body)
        return (
            "Email sent successfully"
            if response.status_code == 200
            else "Failed to send email"
        )

    def _search_google(self, query: str) -> str:
        """Search Google for the given query"""
        return self.serper.run(query)

    def _file_tools(self) -> list[Tool]:
        """Tools for file operations"""
        toolkit: list[Tool] = FileManagementToolkit(
            root_dir=self.base_path, selected_tools=["read_file", "write_file"]
        )
        return toolkit.get_tools()

    async def playwright_tools(self) -> list[Tool]:
        """Tools for playwright operations"""
        playwright = await async_playwright().start()
        browser = await playwright.chromium.launch(headless=False)
        toolkit: PlayWrightBrowserToolkit = PlayWrightBrowserToolkit.from_browser(
            async_browser=browser
        )
        return toolkit.get_tools(), browser, playwright

    async def get_other_tools(self) -> dict[str, Tool]:
        """Get other tools"""
        file_tools: list[Tool] = self._file_tools()
        search_google = Tool(
            name="search_google",
            func=self._search_google,
            description="Search Google for the given query",
        )
        send_email = Tool(
            name="send_email",
            func=self._send_email,
            description="Send an email to the user",
        )
        send_push_notification = Tool(
            name="send_push_notification",
            func=self._send_push_notification,
            description="Send a push notification to the user",
        )
        return {
            "file": file_tools,
            "search": search_google,
            "email": send_email,
            "push_notification": send_push_notification,
        }
