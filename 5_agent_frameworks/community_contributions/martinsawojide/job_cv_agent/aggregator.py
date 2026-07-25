"""Aggregator — output synthesis + inline CVCritic logic.

Receives JobBrief and all committee verdicts directly.
Generates 3 outputs in parallel, then runs the CVCritic revision loop.
"""

import asyncio
import logging
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.messages import TextMessage
from autogen_core import CancellationToken

from messages import (
    ApplicationAnswers, CommitteeVerdict, CritiqueResult, CritiqueResultSchema,
    FinalOutput, JobBrief,
)
from models import sonnet_model

_stage = logging.getLogger("stage")

ALIGN_THRESHOLD, FIDELITY_THRESHOLD, MAX_LOOPS = 7, 8, 2

TYPST_SYSTEM = """You are a professional resume writer producing tailored Typst code.

PERMITTED: reframe bullets with JD keywords, reorder sections, strengthen existing achievements, surface undersold skills.
PROHIBITED: add skills not in ORIGINAL_CV, fabricate titles/companies/dates/outcomes, claim unearned qualifications.

Output ONLY valid Typst code. No markdown fences."""

QA_SYSTEM = (
    "Answer application form questions honestly using only the candidate's actual CV. "
    "Acknowledge genuine gaps rather than bluffing. "
    "For each answer: lead with the strongest relevant experience, "
    "quantify outcomes where evidence exists, and close with one forward-looking sentence "
    "that connects the candidate's trajectory to the role. "
    "Answers should be 3–5 sentences unless the question is binary (Yes/No). "
    "Mirror the tone and vocabulary of the job description."
)

REPORT_SYSTEM = (
    "Produce a concise Markdown alignment report structured as:\n"
    "## Overall Fit\n"
    "One-line verdict (Strong Hire / Lean Hire / No Hire / Hold) with a 0-10 composite score "
    "and one-sentence rationale.\n\n"
    "## Committee Breakdown\n"
    "| Dimension | Score | Hire Label | Top Objection |\n"
    "| --- | --- | --- | --- |\n"
    "One row per committee.\n\n"
    "## Strengths to Amplify\n"
    "3–5 bullets linking candidate strengths directly to JD requirements.\n\n"
    "## Gaps to Address\n"
    "3–5 bullets with each gap and a concrete mitigation (skill-building path, "
    "reference question, or proof-of-work challenge).\n\n"
    "## Interview Talking Points\n"
    "5 questions the hiring manager is likely to ask, with a suggested framing for each answer."
)

CRITIC_SYSTEM = (
    "Evaluate a tailored resume on three axes:\n"
    "alignment_score (0-10): JD keyword/requirement match.\n"
    "fidelity_score (0-10): faithfulness to ORIGINAL_CV. Any fabrication reduces score.\n"
    "positioning_score (0-10): strength of narrative positioning for the specific target role.\n"
    "List all fabricated_claims. Provide revision_instructions with three sections:\n"
    "LANGUAGE IMPROVEMENTS, FABRICATION REVERSIONS, and POSITIONING UPGRADES."
)


class Aggregator:
    def __init__(self, typst_template: str = "") -> None:
        self._typst_template = typst_template
        self._typst_d = AssistantAgent("typst_w", model_client=sonnet_model(), system_message=TYPST_SYSTEM)
        self._qa_d = AssistantAgent("qa_w", model_client=sonnet_model(), system_message=QA_SYSTEM,
                                    output_content_type=ApplicationAnswers)
        self._report_d = AssistantAgent("report_w", model_client=sonnet_model(), system_message=REPORT_SYSTEM)
        self._critic_d = AssistantAgent("critic_d", model_client=sonnet_model(), system_message=CRITIC_SYSTEM,
                                        output_content_type=CritiqueResultSchema)
        self._cv_text = ""
        self._brief: JobBrief | None = None

    async def synthesise(self, brief: JobBrief, verdicts: list[CommitteeVerdict]) -> FinalOutput:
        self._brief = brief
        self._cv_text = brief.cv_text

        verdicts_text = "\n\n".join(
            f"[{v.committee_name}]\n{v.model_dump_json(indent=2)}" for v in verdicts
        )

        # 3 parallel outputs
        typst_p = (f"ORIGINAL_CV:\n{self._cv_text[:4000]}\n\nCOMMITTEE_VERDICTS:\n{verdicts_text}\n\n"
                   + (f"TYPST_TEMPLATE:\n{self._typst_template}\n\n" if self._typst_template
                      else "Create a clean professional Typst resume from scratch.\n\n")
                   + "Generate the tailored Typst resume code now.")

        questions = brief.form_questions
        qa_p = (f"CV:\n{self._cv_text[:3000]}\n\nVERDICTS:\n{verdicts_text}\n\n"
                + ("QUESTIONS:\n" + "\n".join(f"- {q}" for q in questions) + "\nAnswer each."
                   if questions else "Generate likely interview Q&A."))

        report_p = (f"JOB:\n{brief.job_text[:1500]}\n\nCV:\n{self._cv_text[:2000]}\n\n"
                    f"VERDICTS:\n{verdicts_text}\n\nGenerate alignment report.")

        token = CancellationToken()
        results = await asyncio.gather(
            self._typst_d.on_messages([TextMessage(content=typst_p, source="user")], token),
            self._qa_d.on_messages([TextMessage(content=qa_p, source="user")], token),
            self._report_d.on_messages([TextMessage(content=report_p, source="user")], token),
            return_exceptions=True,
        )

        typst_code = _strip_fences(_safe_str(results[0])) if not isinstance(results[0], Exception) else ""

        qa_content = results[1].chat_message.content if not isinstance(results[1], Exception) else ""
        if isinstance(qa_content, ApplicationAnswers):
            qa_text = "\n\n".join(f"Q: {p.question}\nA: {p.answer}" for p in qa_content.qa_pairs)
        else:
            qa_text = str(qa_content)

        report_md = _safe_str(results[2]) if not isinstance(results[2], Exception) else ""

        # CVCritic loop
        _stage.info("[STAGE] Reviewing resume...")
        for loop in range(MAX_LOOPS + 1):
            critique = await self._evaluate(typst_code, token)
            if critique.alignment_score >= ALIGN_THRESHOLD and critique.fidelity_score >= FIDELITY_THRESHOLD:
                print(f"Aggregator: critic APPROVED (align={critique.alignment_score}, fidelity={critique.fidelity_score}, positioning={critique.positioning_score})")
                break
            if loop >= MAX_LOOPS:
                print(f"Aggregator: max revisions — accepting (align={critique.alignment_score}, fidelity={critique.fidelity_score}, positioning={critique.positioning_score})")
                report_md += f"\n\n---\n**WARNING**: Accepted after {MAX_LOOPS} loops. Fabricated: {critique.fabricated_claims}"
                break
            print(f"Aggregator: revision {loop + 1}/{MAX_LOOPS}")
            typst_code = await self._revise(typst_code, critique, token)

        return FinalOutput(typst_code=typst_code, qa_text=qa_text, report_md=report_md)

    async def fix_typst(self, code: str, error: str) -> str:
        prompt = (f"ORIGINAL_CV:\n{self._cv_text[:4000]}\n\n"
                  f"CURRENT TYPST:\n{code}\n\n"
                  f"COMPILE ERROR:\n{error}\n\n"
                  f"Fix the Typst so it compiles. Output ONLY corrected Typst code.")
        resp = await self._typst_d.on_messages([TextMessage(content=prompt, source="user")], CancellationToken())
        return _strip_fences(_safe_str(resp))

    async def _evaluate(self, typst_code: str, token: CancellationToken) -> CritiqueResult:
        prompt = (f"ORIGINAL_CV:\n{self._cv_text[:4000]}\n\n"
                  f"JOB:\n{self._brief.job_text[:2000]}\n\n"
                  f"TYPST_DRAFT:\n{typst_code[:6000]}\n\nEvaluate.")
        resp = await self._critic_d.on_messages([TextMessage(content=prompt, source="user")], token)
        s = resp.chat_message.content
        if isinstance(s, CritiqueResultSchema):
            return CritiqueResult(
                alignment_score=s.alignment_score, fidelity_score=s.fidelity_score,
                positioning_score=s.positioning_score,
                fabricated_claims=s.fabricated_claims, revision_instructions=s.revision_instructions,
            )
        return CritiqueResult(alignment_score=5, fidelity_score=5, revision_instructions=str(s))

    async def _revise(self, code: str, critique: CritiqueResult, token: CancellationToken) -> str:
        prompt = (f"ORIGINAL_CV:\n{self._cv_text[:4000]}\n\nCURRENT:\n{code}\n\n"
                  f"REVISIONS:\n{critique.revision_instructions}\n\n")
        if critique.fabricated_claims:
            prompt += "REVERT:\n" + "\n".join(f"- {c}" for c in critique.fabricated_claims) + "\n\n"
        prompt += "Output ONLY corrected Typst code."
        resp = await self._typst_d.on_messages([TextMessage(content=prompt, source="user")], token)
        return _strip_fences(_safe_str(resp))


def _safe_str(resp) -> str:
    if isinstance(resp, Exception):
        return ""
    content = resp.chat_message.content
    return str(content) if not isinstance(content, str) else content

def _strip_fences(text: str) -> str:
    s = text.strip()
    if s.startswith("```"):
        lines = s.split("\n")
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        return "\n".join(lines)
    return s
