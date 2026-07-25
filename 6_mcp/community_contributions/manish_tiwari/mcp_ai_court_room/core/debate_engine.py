"""Three-round debate with MCP case research and token streaming to the UI."""

from __future__ import annotations

from dataclasses import dataclass
from typing import AsyncIterator

from rich.console import Console

from agents.case_research_agent import CaseResearchAgent
from agents.judge_agent import JudgeAgent
from agents.lawyer_against_agent import LawyerAgainstAgent
from agents.lawyer_pro_agent import LawyerProAgent
from core.mcp_session import courtroom_mcp_session
from core.state import CaseBrief, DebateState, DebateTurn, Judgement
from langchain_core.language_models.chat_models import BaseChatModel
from llm.llm_router import chat_model_for_role
from tools.case_search_tool import default_latest_legal_search_query

console = Console()


@dataclass
class CourtroomUIState:
    """Flat strings for Gradio Textboxes (left / center / right)."""

    case_md: str
    lawyer1_text: str
    judge_text: str
    lawyer2_text: str
    status: str
    raw_state: DebateState


def _case_markdown(c: CaseBrief) -> str:
    return f"""### {c.case_title}

**Legal issue:** {c.legal_issue}

**Plaintiff:** {c.plaintiff}

**Defendant:** {c.defendant}

**Summary:** {c.summary}
"""


class DebateEngine:
    """Orchestrates research → 3×(pro stream, against stream, judge stream) → streamed final verdict."""

    def __init__(
        self,
        llm_research: BaseChatModel | None = None,
        llm_pro: BaseChatModel | None = None,
        llm_against: BaseChatModel | None = None,
        llm_judge: BaseChatModel | None = None,
    ) -> None:
        self.llm_research = llm_research or chat_model_for_role("research")
        self.llm_pro = llm_pro or chat_model_for_role("pro")
        self.llm_against = llm_against or chat_model_for_role("against")
        self.llm_judge = llm_judge or chat_model_for_role("judge")

    def _ui(
        self,
        state: DebateState,
        lawyer1: str,
        judge_t: str,
        lawyer2: str,
        status: str,
    ) -> CourtroomUIState:
        case_md = _case_markdown(state.case) if state.case else "_Resolving docket…_"
        return CourtroomUIState(
            case_md=case_md,
            lawyer1_text=lawyer1,
            judge_text=judge_t,
            lawyer2_text=lawyer2,
            status=status,
            raw_state=state,
        )

    async def _stream_debate_rounds(
        self,
        state: DebateState,
        lawyer1: str,
        judge_t: str,
        lawyer2: str,
    ) -> AsyncIterator[CourtroomUIState]:
        """Run rounds 1–3 and final verdict; uses nonlocal-style mutation via yielded snapshots."""
        transcript_parts: list[str] = []
        pro_agent = LawyerProAgent()
        against_agent = LawyerAgainstAgent()
        judge_agent = JudgeAgent()
        assert state.case is not None

        for round_num in range(1, 4):
            prior = "\n".join(transcript_parts)

            lawyer1 += f"\n\n**Round {round_num} — Counsel for plaintiff**\n\n"
            yield self._ui(
                state,
                lawyer1,
                judge_t,
                lawyer2,
                f"Round {round_num} — plaintiff counsel (streaming)",
            )
            pro_buf: list[str] = []
            async for delta in pro_agent.argue_stream(
                self.llm_pro, state.case, prior, round_num
            ):
                pro_buf.append(delta)
                lawyer1 += delta
                yield self._ui(
                    state,
                    lawyer1,
                    judge_t,
                    lawyer2,
                    f"Round {round_num} — plaintiff counsel (streaming)",
                )
            pro_arg = "".join(pro_buf).strip()
            state.turns.append(DebateTurn(round_num=round_num, role="pro", content=pro_arg))
            transcript_parts.append(f"PRO (R{round_num}): {pro_arg}")

            lawyer2 += f"\n\n**Round {round_num} — Counsel for defense**\n\n"
            yield self._ui(
                state,
                lawyer1,
                judge_t,
                lawyer2,
                f"Round {round_num} — defense counsel (streaming)",
            )
            def_buf: list[str] = []
            async for delta in against_agent.argue_stream(
                self.llm_against,
                state.case,
                "\n".join(transcript_parts),
                round_num,
            ):
                def_buf.append(delta)
                lawyer2 += delta
                yield self._ui(
                    state,
                    lawyer1,
                    judge_t,
                    lawyer2,
                    f"Round {round_num} — defense counsel (streaming)",
                )
            con_arg = "".join(def_buf).strip()
            state.turns.append(
                DebateTurn(round_num=round_num, role="against", content=con_arg)
            )
            transcript_parts.append(f"AGAINST (R{round_num}): {con_arg}")

            judge_t += f"\n\n**Round {round_num} — Bench observation**\n\n"
            yield self._ui(
                state,
                lawyer1,
                judge_t,
                lawyer2,
                f"Round {round_num} — bench (streaming)",
            )
            obs_buf: list[str] = []
            async for delta in judge_agent.observe_stream(
                self.llm_judge,
                state.case,
                "\n".join(transcript_parts),
                round_num,
            ):
                obs_buf.append(delta)
                judge_t += delta
                yield self._ui(
                    state,
                    lawyer1,
                    judge_t,
                    lawyer2,
                    f"Round {round_num} — bench (streaming)",
                )
            obs = "".join(obs_buf).strip()
            state.judge_comments.append(obs)
            state.turns.append(DebateTurn(round_num=round_num, role="judge", content=obs))
            transcript_parts.append(f"JUDGE (R{round_num}): {obs}")

        judge_t += "\n\n---\n\n## FINAL VERDICT\n\n"
        yield self._ui(
            state,
            lawyer1,
            judge_t,
            lawyer2,
            "Court in recess — drafting final judgement (streaming)",
        )
        full_transcript = "\n".join(transcript_parts)
        verdict_body: list[str] = []
        async for delta in judge_agent.final_judgement_stream(
            self.llm_judge, state.case, full_transcript
        ):
            verdict_body.append(delta)
            judge_t += delta
            yield self._ui(
                state,
                lawyer1,
                judge_t,
                lawyer2,
                "Court in recess — drafting final judgement (streaming)",
            )
        body = "".join(verdict_body).strip()
        try:
            state.final = judge_agent.parse_streamed_verdict(body)
        except Exception:
            state.final = Judgement(
                reasoning="Parse fallback",
                winner="split",
                judgement=body[:2000] or "—",
            )

        yield self._ui(state, lawyer1, judge_t, lawyer2, "Session complete")

    async def run_streaming(
        self,
        optional_case_details: str | None = None,
    ) -> AsyncIterator[CourtroomUIState]:
        lawyer1 = ""
        lawyer2 = ""
        judge_t = ""
        state = DebateState()
        notes = (optional_case_details or "").strip()

        async def drive_debate() -> AsyncIterator[CourtroomUIState]:
            nonlocal lawyer1, lawyer2, judge_t
            async for snap in self._stream_debate_rounds(state, lawyer1, judge_t, lawyer2):
                lawyer1 = snap.lawyer1_text
                lawyer2 = snap.lawyer2_text
                judge_t = snap.judge_text
                yield snap

        try:
            if notes:
                yield self._ui(
                    state, lawyer1, judge_t, lawyer2, "Structuring case from your notes…"
                )
                researcher = CaseResearchAgent()
                state.case = await researcher.from_user_text(self.llm_research, notes)
                yield self._ui(
                    state, lawyer1, judge_t, lawyer2, "Case locked — opening session"
                )
                async for snap in drive_debate():
                    yield snap
            else:
                yield self._ui(
                    state, lawyer1, judge_t, lawyer2, "Connecting MCP server…"
                )
                async with courtroom_mcp_session() as session:
                    yield self._ui(
                        state,
                        lawyer1,
                        judge_t,
                        lawyer2,
                        "Searching latest matters (web + today's date in query)…",
                    )
                    researcher = CaseResearchAgent()
                    q = default_latest_legal_search_query()
                    state.case = await researcher.run(
                        session, self.llm_research, search_query=q
                    )
                    yield self._ui(
                        state,
                        lawyer1,
                        judge_t,
                        lawyer2,
                        "Case locked — opening session",
                    )
                    async for snap in drive_debate():
                        yield snap
        except Exception as exc:  # noqa: BLE001
            console.print(f"[red]Debate error:[/red] {exc}")
            state.case = state.case or CaseBrief(
                case_title="Session error",
                summary=str(exc),
                legal_issue="Could not complete research or debate",
                plaintiff="N/A",
                defendant="N/A",
            )
            judge_t += f"\n\n**Error**\n\n{exc}"
            yield self._ui(state, lawyer1, judge_t, lawyer2, f"Error: {exc}")

    def run_sync_snapshot(
        self, optional_case_details: str | None = None
    ) -> CourtroomUIState:
        """Synchronous helper for tests (runs full asyncio loop internally)."""
        import asyncio

        final: CourtroomUIState | None = None

        async def _consume():
            nonlocal final
            async for snap in self.run_streaming(optional_case_details=optional_case_details):
                final = snap

        asyncio.run(_consume())
        assert final is not None
        return final
