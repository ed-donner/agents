"""Judge: mid-debate observations and final structured judgement."""

from __future__ import annotations

import json
import re
from collections.abc import AsyncIterator

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage

from agents.streaming_utils import chunk_text
from core.state import CaseBrief, Judgement


class JudgeAgent:
    OBSERVE_SYSTEM = """You are a trial judge moderating written arguments.
Give a concise bench observation (2 sentences): note strengths/weaknesses, no final ruling."""

    FINAL_SYSTEM = """You are the presiding judge. Weigh both sides fairly using sound legal reasoning.
Return JSON only with keys: reasoning (string), winner (one of: pro, against, split), judgement (string verdict paragraph)."""

    async def observe(
        self,
        llm: BaseChatModel,
        case: CaseBrief,
        transcript: str,
        round_num: int,
    ) -> str:
        human = f"""Round {round_num} observation.
CASE: {case.case_title} — {case.legal_issue}

TRANSCRIPT:
{transcript}"""
        msg = await llm.ainvoke(
            [SystemMessage(content=self.OBSERVE_SYSTEM), HumanMessage(content=human)]
        )
        return self._to_text(msg)

    async def observe_stream(
        self,
        llm: BaseChatModel,
        case: CaseBrief,
        transcript: str,
        round_num: int,
    ) -> AsyncIterator[str]:
        human = f"""Round {round_num} observation.
CASE: {case.case_title} — {case.legal_issue}

TRANSCRIPT:
{transcript}"""
        messages = [
            SystemMessage(content=self.OBSERVE_SYSTEM),
            HumanMessage(content=human),
        ]
        async for chunk in llm.astream(messages):
            delta = chunk_text(chunk)
            if delta:
                yield delta

    FINAL_STREAM_SYSTEM = """You are the presiding judge. Weigh both sides with clear, fair legal reasoning.
Write exactly three labeled sections (plain text, no JSON):
REASONING: (paragraph)
WINNER: one of pro | against | split
JUDGEMENT: (final paragraph verdict)"""

    async def final_judgement_stream(
        self, llm: BaseChatModel, case: CaseBrief, full_transcript: str
    ) -> AsyncIterator[str]:
        """Stream human-readable verdict; use parse_streamed_verdict on full text."""
        human = f"""CASE BRIEF:
{case.model_dump_json(indent=2)}

FULL DEBATE:
{full_transcript}

Deliver your ruling in the three labeled sections."""
        messages = [
            SystemMessage(content=self.FINAL_STREAM_SYSTEM),
            HumanMessage(content=human),
        ]
        async for chunk in llm.astream(messages):
            delta = chunk_text(chunk)
            if delta:
                yield delta

    @staticmethod
    def parse_streamed_verdict(text: str) -> Judgement:
        """Parse REASONING / WINNER / JUDGEMENT blocks into Judgement."""
        reasoning_m = re.search(
            r"REASONING:\s*(.+?)(?=WINNER:|$)", text, re.DOTALL | re.IGNORECASE
        )
        winner_m = re.search(
            r"WINNER:\s*(pro|against|split)\b",
            text,
            re.IGNORECASE,
        )
        judgement_m = re.search(
            r"JUDGEMENT:\s*(.+)$", text, re.DOTALL | re.IGNORECASE
        )
        reasoning = (reasoning_m.group(1).strip() if reasoning_m else text[:800]).strip()
        winner_raw = (winner_m.group(1).strip().lower() if winner_m else "split")
        judgement = (judgement_m.group(1).strip() if judgement_m else text[-1200:]).strip()
        return Judgement(reasoning=reasoning, winner=winner_raw, judgement=judgement)

    async def final_judgement(
        self, llm: BaseChatModel, case: CaseBrief, full_transcript: str
    ) -> Judgement:
        human = f"""CASE BRIEF:
{case.model_dump_json(indent=2)}

FULL DEBATE:
{full_transcript}

Deliver judgement JSON as specified."""
        try:
            structured = llm.with_structured_output(Judgement)
            return await structured.ainvoke(
                [SystemMessage(content=self.FINAL_SYSTEM), HumanMessage(content=human)]
            )
        except Exception:
            return await self._parse_final(llm, human)

    async def _parse_final(self, llm: BaseChatModel, human: str) -> Judgement:
        msg = await llm.ainvoke(
            [SystemMessage(content=self.FINAL_SYSTEM), HumanMessage(content=human)]
        )
        text = self._to_text(msg)
        match = re.search(r"\{[\s\S]*\}", text)
        if not match:
            return Judgement(
                reasoning="Model returned non-JSON; defaulting to split.",
                winner="split",
                judgement=text[:2000],
            )
        data = json.loads(match.group())
        return Judgement(**data)

    @staticmethod
    def _to_text(msg) -> str:
        content = msg.content
        if isinstance(content, list):
            return "".join(
                getattr(x, "text", str(x)) if not isinstance(x, str) else x
                for x in content
            )
        return str(content).strip()
