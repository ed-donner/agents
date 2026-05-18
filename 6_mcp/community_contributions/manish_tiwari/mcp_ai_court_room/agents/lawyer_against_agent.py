"""Lawyer arguing against the claimant / in support of the defense."""

from __future__ import annotations

from collections.abc import AsyncIterator

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage

from agents.streaming_utils import chunk_text
from core.state import CaseBrief


class LawyerAgainstAgent:
    SYSTEM = """You are a senior advocate arguing AGAINST the claimant position.
Use counter-precedents, procedural angles, and constitutional counterpoints where apt.
Reply with 2-3 short sentences only, no bullet labels."""

    async def argue(
        self,
        llm: BaseChatModel,
        case: CaseBrief,
        prior_transcript: str,
        round_num: int,
    ) -> str:
        human = f"""Round {round_num}.
CASE:
Title: {case.case_title}
Issue: {case.legal_issue}
Summary: {case.summary}
Plaintiff: {case.plaintiff}
Defendant: {case.defendant}

DEBATE SO FAR:
{prior_transcript or '(opening round)'}

Rebut and weaken opposing counsel's strongest points."""
        msg = await llm.ainvoke(
            [SystemMessage(content=self.SYSTEM), HumanMessage(content=human)]
        )
        content = msg.content
        if isinstance(content, list):
            return "".join(
                getattr(x, "text", str(x)) if not isinstance(x, str) else x
                for x in content
            )
        return str(content).strip()

    def _messages(
        self, case: CaseBrief, prior_transcript: str, round_num: int
    ) -> list:
        human = f"""Round {round_num}.
CASE:
Title: {case.case_title}
Issue: {case.legal_issue}
Summary: {case.summary}
Plaintiff: {case.plaintiff}
Defendant: {case.defendant}

DEBATE SO FAR:
{prior_transcript or '(opening round)'}

Rebut and weaken opposing counsel's strongest points."""
        return [SystemMessage(content=self.SYSTEM), HumanMessage(content=human)]

    async def argue_stream(
        self,
        llm: BaseChatModel,
        case: CaseBrief,
        prior_transcript: str,
        round_num: int,
    ) -> AsyncIterator[str]:
        messages = self._messages(case, prior_transcript, round_num)
        async for chunk in llm.astream(messages):
            delta = chunk_text(chunk)
            if delta:
                yield delta
