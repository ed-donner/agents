"""Case research agent: uses MCP tools then structures a CaseBrief via LLM."""

from __future__ import annotations

import json
import re

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.language_models.chat_models import BaseChatModel

from core.mcp_session import mcp_result_to_text
from core.state import CaseBrief
from tools.case_search_tool import default_latest_legal_search_query


class CaseResearchAgent:
    """Fetches raw material through MCP, then asks the LLM to normalize fields."""

    SYSTEM = """You are a legal research clerk. Given web search bundles about law and courts,
you must output a single factual case brief. Use only what the sources plausibly support.
If parties are unclear, name them as 'Unknown (see sources)' rather than inventing names.
legal_issue must be one crisp question of law or dispute."""

    USER_NOTES_SYSTEM = """You are a legal research clerk. The user supplied case notes (may be informal).
Produce a neutral case brief: case_title, summary, legal_issue, plaintiff, defendant.
Infer missing facts conservatively; use 'Unknown' when unclear."""

    async def run(
        self,
        session,
        llm: BaseChatModel,
        *,
        search_query: str | None = None,
    ) -> CaseBrief:
        q = search_query or default_latest_legal_search_query()
        raw_search = await session.call_tool(
            "search_case",
            arguments={"query": q},
        )
        bundle = mcp_result_to_text(raw_search)
        try:
            payload = json.loads(bundle)
        except json.JSONDecodeError:
            payload = {"combined_text": bundle}

        combined = payload.get("combined_text") or bundle
        head = combined[:800].replace("\n", " ")

        deeper = await session.call_tool(
            "fetch_case_summary",
            arguments={"case_reference": head[:400]},
        )
        extra = mcp_result_to_text(deeper)
        try:
            extra_payload = json.loads(extra)
            extra_text = extra_payload.get("summary_text") or extra
        except json.JSONDecodeError:
            extra_text = extra

        user_prompt = f"""SOURCES (may be noisy):\n{combined}\n\nDEEPER PASS:\n{extra_text}

Produce JSON with keys: case_title, summary, legal_issue, plaintiff, defendant.
Respond with JSON only, no markdown."""

        structured = llm.with_structured_output(CaseBrief)
        try:
            return await structured.ainvoke(
                [
                    SystemMessage(content=self.SYSTEM),
                    HumanMessage(content=user_prompt),
                ]
            )
        except Exception:
            return await self._fallback_parse(llm, user_prompt)

    async def from_user_text(self, llm: BaseChatModel, user_text: str) -> CaseBrief:
        """Build CaseBrief from user-provided notes (no MCP / web search)."""
        text = user_text.strip()
        prompt = f"""CASE NOTES FROM USER:
{text}

Output structured case brief fields only."""
        structured = llm.with_structured_output(CaseBrief)
        try:
            return await structured.ainvoke(
                [
                    SystemMessage(content=self.USER_NOTES_SYSTEM),
                    HumanMessage(content=prompt),
                ]
            )
        except Exception:
            return await self._fallback_parse(llm, prompt, clerk_system=self.USER_NOTES_SYSTEM)

    async def _fallback_parse(
        self,
        llm: BaseChatModel,
        user_prompt: str,
        *,
        clerk_system: str | None = None,
    ) -> CaseBrief:
        sys = (clerk_system or self.SYSTEM) + " Output raw JSON only."
        resp = await llm.ainvoke(
            [
                SystemMessage(content=sys),
                HumanMessage(content=user_prompt),
            ]
        )
        text = getattr(resp, "content", str(resp))
        if isinstance(text, list):
            text = "".join(
                getattr(x, "text", str(x)) if not isinstance(x, str) else x for x in text
            )
        match = re.search(r"\{[\s\S]*\}", text)
        if not match:
            return CaseBrief(
                case_title="Legal matter (parse fallback)",
                summary=text[:1200],
                legal_issue="To be determined from sources",
                plaintiff="Unknown (see sources)",
                defendant="Unknown (see sources)",
            )
        data = json.loads(match.group())
        return CaseBrief(**data)
