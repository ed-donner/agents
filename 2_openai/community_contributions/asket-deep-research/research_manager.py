import asyncio
import logging
import os

from agents import Runner, trace, gen_trace_id, InputGuardrailTripwireTriggered
from openai import APIError, APITimeoutError, APIConnectionError

from search_agent import search_agent
from planner_agent import planner_agent, WebSearchItem, WebSearchPlan
from writer_agent import writer_agent, ReportData
from email_agent import email_agent, recipient_override

logger = logging.getLogger(__name__)


class ResearchError(Exception):
    pass


class ResearchManager:
    def __init__(self, send_email_report: bool = True, recipient_email: str | None = None):
        self.send_email_report = send_email_report
        self.recipient_email = (recipient_email or "").strip() or None

    async def run(self, query: str):
        trace_id = gen_trace_id()
        trace_url = f"https://platform.openai.com/traces/trace?trace_id={trace_id}"

        with trace("Research trace", trace_id=trace_id):
            try:
                yield f"🔗 [View trace]({trace_url})\n\n"
                yield "⏳ **Starting research...**\n\n"

                search_plan = await self._plan_searches(query)
                yield f"📋 **Planned {len(search_plan.searches)} searches**\n\n"

                search_results = await self._perform_searches(search_plan)
                yield f"✅ **Searches complete** ({len(search_results)} results)\n\n"
                yield "✍️ **Writing report...**\n\n"

                report = await self._write_report(query, search_results)
                yield "📄 **Report written**\n\n"

                if self.send_email_report:
                    if not self.recipient_email and not os.environ.get("SENDGRID_TO"):
                        yield (
                            "⚠️ **Email not sent:** enter your email in the app or set `SENDGRID_TO` "
                            "in your environment.\n\n"
                        )
                    else:
                        try:
                            await self._send_email(report)
                            yield "📧 **Email sent**\n\n"
                        except Exception as e:
                            logger.warning("Email send failed: %s", e)
                            yield f"⚠️ **Email not sent** ({e})\n\n"

                yield "---\n\n"
                yield report.markdown_report

            except InputGuardrailTripwireTriggered as e:
                yield f"❌ **Blocked by input guardrail:** {e}\n\n"
                raise ResearchError("Input guardrail triggered") from e
            except APITimeoutError as e:
                logger.error("API timeout: %s", e)
                yield f"❌ **Request timed out.** Please try again.\n\n"
                raise ResearchError("API timeout") from e
            except APIConnectionError as e:
                logger.error("Connection error: %s", e)
                yield f"❌ **Connection error.** Check your network.\n\n"
                raise ResearchError("Connection error") from e
            except APIError as e:
                logger.exception("API error: %s", e)
                yield f"❌ **API error:** {str(e)[:200]}\n\n"
                raise ResearchError(f"API error: {e}") from e
            except Exception as e:
                logger.exception("Unexpected error: %s", e)
                yield f"❌ **Error:** {str(e)[:200]}\n\n"
                raise ResearchError(str(e)) from e

    async def _plan_searches(self, query: str) -> WebSearchPlan:
        result = await Runner.run(
            planner_agent,
            f"Query: {query}",
            max_turns=5,
        )
        return result.final_output_as(WebSearchPlan)

    async def _perform_searches(self, search_plan: WebSearchPlan) -> list[str]:
        tasks = [asyncio.create_task(self._search(item)) for item in search_plan.searches]
        results = []
        for task in asyncio.as_completed(tasks):
            try:
                result = await task
                if result is not None:
                    results.append(result)
            except Exception as e:
                logger.warning("Search failed: %s", e)
        return results

    async def _search(self, item: WebSearchItem) -> str | None:
        input_text = f"Search term: {item.query}\nReason for searching: {item.reason}"
        try:
            result = await Runner.run(search_agent, input_text, max_turns=5)
            return str(result.final_output)
        except Exception as e:
            logger.warning("Search failed for %s: %s", item.query, e)
            return None

    async def _write_report(self, query: str, search_results: list[str]) -> ReportData:
        input_text = f"Original query: {query}\nSummarized search results: {search_results}"
        result = await Runner.run(
            writer_agent,
            input_text,
            max_turns=10,
        )
        return result.final_output_as(ReportData)

    async def _send_email(self, report: ReportData) -> None:
        token = recipient_override.set(self.recipient_email)
        try:
            await Runner.run(email_agent, report.markdown_report, max_turns=5)
        finally:
            recipient_override.reset(token)
