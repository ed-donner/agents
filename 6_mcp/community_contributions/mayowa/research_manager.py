from contextlib import AsyncExitStack
import os
import shutil
from typing import AsyncGenerator, Literal, TypedDict

from agents import Runner, gen_trace_id, trace
from agents.mcp import MCPServerStdio

from planner import Planner, WebSearchItem
from writer import Writer
from searcher import Searcher
from notification import Notification


class ResearchEvent(TypedDict):
    type: Literal["status", "report", "chat"]
    content: str


class ResearchManager:
    def __init__(self, query: str, clarifying_questions: list[str]):
        self.query = query
        self.writer = Writer(query)
        self.clarifying_questions = clarifying_questions


    @classmethod
    def research_mcp_server_params(cls) -> list[dict]:
        brave_api_key = os.getenv("BRAVE_API_KEY")
        if not brave_api_key:
            raise RuntimeError(
                "BRAVE_API_KEY is not configured. Add it to your environment before running this app."
            )

        params = []
        fetch_params = cls.fetch_mcp_server_params()
        if fetch_params is not None:
            params.append(fetch_params)

        params.append(
            {
                "command": "npx",
                "args": ["-y", "@modelcontextprotocol/server-brave-search"],
                "env": {"BRAVE_API_KEY": brave_api_key},
            }
        )
        return params


    @staticmethod
    def fetch_mcp_server_params() -> dict | None:
        fetch_binary = shutil.which("mcp-server-fetch")
        if fetch_binary:
            return {"command": fetch_binary, "args": []}

        uvx_binary = shutil.which("uvx")
        if uvx_binary:
            return {"command": uvx_binary, "args": ["mcp-server-fetch"]}

        return None


    async def run(self) -> AsyncGenerator[ResearchEvent, None]:
        trace_id = gen_trace_id()
        with trace("Research trace", trace_id=trace_id):
            trace_url = f"https://platform.openai.com/traces/trace?trace_id={trace_id}"
            yield {"type": "status", "content": f"View trace: {trace_url}"}

            async with AsyncExitStack() as stack:
                research_mcp_servers = [
                    await stack.enter_async_context(
                        MCPServerStdio(
                            params,
                            client_session_timeout_seconds=50,
                        )
                    )
                    for params in ResearchManager.research_mcp_server_params()
                ]

                print("Starting research...")
                planner = Planner(
                    clarifying_questions=self.clarifying_questions,
                    clarifying_answers=self.clarifying_answers,
                )
                search_plan = await planner.run(self.query)
                yield {
                    "type": "status",
                    "content": f"\nSearches planned. Starting web research with {len(search_plan.searches)} searches."
                }

                searcher = Searcher(research_mcp_servers)
                search_results: list[str] = []
                total_searches = len(search_plan.searches)
                for index, item in enumerate(search_plan.searches, start=1):
                    yield {
                        "type": "status",
                        "content": f"\nRunning search {index}/{total_searches}: {item.query}",
                    }
                    summary = await searcher.run(item)
                    search_results.append(
                        "\n".join(
                            [
                                f"Search #{index}: {item.query}",
                                f"Why this search matters: {item.reason}",
                                summary,
                            ]
                        )
                    )
                    yield {
                        "type": "status",
                        "content": f"\nCompleted search {index}/{total_searches}: {item.query}",
                    }
                yield {"type": "status", "content": "Searches complete. Writing report..."}

                async for report in self.writer.run(search_results):
                    yield {"type": "report", "content": report}

                yield {"type": "chat", "content": "Report written, sending push notification..."}

                await Notification.push(report)
                yield {"type": "chat", "content": "Push notification sent, research complete."}
