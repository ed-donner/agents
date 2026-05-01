from agents import Agent, Runner, trace, gen_trace_id
from openai.types.responses import ResponseTextDeltaEvent
from typing import AsyncGenerator, Literal, TypedDict
from pydantic import BaseModel, Field
from planner import Planner
from email_agent import email_agent
from report_generator import ReportGenerator


class ResearchEvent(TypedDict):
    type: Literal["status", "report"]
    content: str



class ResearchManager:
    def __init__(self, query: str, clarifying_questions: list[str]):
        self.query = query
        self.clarifying_questions = clarifying_questions


    async def run(self) -> AsyncGenerator[ResearchEvent, None]:
        """Run deep research and emit status and report events."""
        trace_id = gen_trace_id()
        with trace("Research trace", trace_id=trace_id):
            trace_url = f"https://platform.openai.com/traces/trace?trace_id={trace_id}"
            print(f"View trace: {trace_url}")
            yield {"type": "status", "content": f"View trace: {trace_url}"}

            print("Starting research...")
            planner = Planner(clarifying_questions=self.clarifying_questions, clarifying_answers=self.clarifying_answers)
            search_plan = await planner.run(self.query)
            yield {"type": "status", "content": f"\nSearches planned, starting to search... {len(search_plan.searches)} searches to perform"}

            generator = ReportGenerator(self.query, search_plan)
            report = ''

            async for event in generator.run().stream_events():
                if event.type == 'raw_response_event' and isinstance(event.data, ResponseTextDeltaEvent):
                    report += event.data.delta
                    yield {"type": "report", "content": report}

            yield {"type": "chat", "content": "Report written, sending email..."}
            await self.send_email(report)
            yield {"type": "chat", "content": "Email sent, research complete."}


    async def send_email(self, report: str) -> None:
        print("Writing email...")
        result = await Runner.run(
            email_agent,
            report,
        )
        print("Email sent")
