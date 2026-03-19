from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


AllowedAction = Literal["clarify", "research", "evaluate", "write_report", "stop"]


class ClarificationQuestions(BaseModel):
    questions: list[str] = Field(
        description="Exactly three clarifying questions that refine the research scope.",
        min_length=3,
        max_length=3,
    )


class EvidenceItem(BaseModel):
    source: str = Field(description="The cited source or publication name.")
    url: str = Field(description="The source URL when available.")
    note: str = Field(description="Why this source matters for the current finding.")


class FindingItem(BaseModel):
    title: str = Field(description="A concise finding headline.")
    summary: str = Field(description="A short synthesis of the finding.")


class ResearchResult(BaseModel):
    search_queries: list[str] = Field(description="The search queries used during this pass.")
    findings: list[FindingItem] = Field(description="The synthesized findings from this pass.")
    evidence: list[EvidenceItem] = Field(description="Supporting evidence collected from sources.")
    gaps: list[str] = Field(description="Important information still missing after this pass.")


class EvaluationResult(BaseModel):
    enough_coverage: bool = Field(description="Whether the current research is sufficient.")
    needs_more_research: bool = Field(description="Whether another research pass is recommended.")
    remaining_gaps: list[str] = Field(description="Important unresolved gaps that still remain.")
    recommended_focus: str = Field(description="The best next focus if more work is needed.")
    reasoning: str = Field(description="Why the evaluator made this decision.")


class FinalReport(BaseModel):
    executive_summary: str
    key_findings: list[str]
    evidence_and_sources: list[str]
    analysis_and_interpretation: str
    uncertainties_or_conflicting_evidence: list[str]
    potential_future_developments: list[str]

    def as_markdown(self) -> str:
        sections = [
            "# Deep Research Report",
            "",
            "## Executive summary",
            self.executive_summary.strip(),
            "",
            "## Key findings",
            *[f"- {item}" for item in self.key_findings],
            "",
            "## Evidence and sources",
            *[f"- {item}" for item in self.evidence_and_sources],
            "",
            "## Analysis and interpretation",
            self.analysis_and_interpretation.strip(),
            "",
            "## Uncertainties or conflicting evidence",
            *[f"- {item}" for item in self.uncertainties_or_conflicting_evidence],
            "",
            "## Potential future developments",
            *[f"- {item}" for item in self.potential_future_developments],
        ]
        return "\n".join(sections).strip()


class OrchestratorDecision(BaseModel):
    next_action: AllowedAction = Field(description="The next valid step for the research workflow.")
    reason: str = Field(description="Why this action is the best next move.")
    focus: str = Field(
        default="",
        description="The specific focus to carry into the next step when relevant.",
    )


class ResearchState(BaseModel):
    original_query: str
    clarification_questions: list[str] = Field(default_factory=list)
    clarification_answers: list[str] = Field(default_factory=list)
    research_results: list[ResearchResult] = Field(default_factory=list)
    evaluator_feedback: list[EvaluationResult] = Field(default_factory=list)
    final_report: FinalReport | None = None
    runtime_notes: list[str] = Field(default_factory=list)
    iteration_count: int = 0
    search_count: int = 0
    max_iterations: int = 2
    max_searches: int = 6

    def latest_research(self) -> ResearchResult | None:
        return self.research_results[-1] if self.research_results else None

    def latest_evaluation(self) -> EvaluationResult | None:
        return self.evaluator_feedback[-1] if self.evaluator_feedback else None

    def unresolved_gaps(self) -> list[str]:
        gaps: list[str] = []
        latest_research = self.latest_research()
        latest_evaluation = self.latest_evaluation()
        if latest_research:
            gaps.extend(latest_research.gaps)
        if latest_evaluation:
            gaps.extend(latest_evaluation.remaining_gaps)
        return list(dict.fromkeys(item.strip() for item in gaps if item.strip()))

    def summary_for_agent(self) -> str:
        latest_research = self.latest_research()
        latest_evaluation = self.latest_evaluation()

        lines = [
            f"Original query: {self.original_query}",
            f"Clarification answers: {self.clarification_answers or 'none'}",
            f"Research passes completed: {len(self.research_results)}",
            f"Iterations used: {self.iteration_count}/{self.max_iterations}",
            f"Searches used: {self.search_count}/{self.max_searches}",
        ]

        if latest_research:
            findings = "; ".join(item.title for item in latest_research.findings[:3]) or "none"
            lines.extend(
                [
                    f"Latest research findings: {findings}",
                    f"Latest research gaps: {latest_research.gaps or 'none'}",
                ]
            )

        if latest_evaluation:
            lines.extend(
                [
                    f"Latest evaluation enough_coverage: {latest_evaluation.enough_coverage}",
                    f"Latest evaluation needs_more_research: {latest_evaluation.needs_more_research}",
                    f"Latest evaluation focus: {latest_evaluation.recommended_focus}",
                ]
            )

        if self.runtime_notes:
            lines.append(f"Runtime notes: {self.runtime_notes[-3:]}")

        return "\n".join(lines)
