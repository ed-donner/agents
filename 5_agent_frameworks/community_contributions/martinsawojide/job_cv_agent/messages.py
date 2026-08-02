from __future__ import annotations
from pydantic import BaseModel, Field


# Inter-agent messages

class JobBrief(BaseModel):
    job_text: str
    apply_url: str | None = None
    form_questions: list[str] = Field(default_factory=list)
    company_profile: str = ""
    cv_text: str = ""
    cv_typst: str = ""
    priority_weights: str = "technical:0.4, product:0.3, leadership:0.2, fit:0.1"

class CommitteeVerdict(BaseModel):
    committee_name: str
    pros: str
    cons: str
    score: int = Field(ge=0, le=10)
    confidence_pct: int = Field(ge=0, le=100, default=70)
    hire_label: str = ""
    summary: str
    top_objection: str = ""
    mitigation: str = ""
    cv_gaps: list[str] = Field(default_factory=list)

class CritiqueResult(BaseModel):
    alignment_score: int = Field(ge=0, le=10)
    fidelity_score: int = Field(ge=0, le=10)
    positioning_score: int = Field(ge=0, le=10, default=5)
    fabricated_claims: list[str] = Field(default_factory=list)
    revision_instructions: str = ""

class FinalOutput(BaseModel):
    typst_code: str = ""
    qa_text: str = ""
    report_md: str = ""


# Structured output schemas (for output_content_type)

class JobPosting(BaseModel):
    title: str = ""
    company: str = ""
    location: str = ""
    requirements: list[str] = Field(default_factory=list)
    responsibilities: list[str] = Field(default_factory=list)
    form_questions: list[str] = Field(default_factory=list)
    raw_text: str = ""

class AllPersonas(BaseModel):
    technical_advocate: str = ""
    technical_skeptic: str = ""
    experience_advocate: str = ""
    experience_skeptic: str = ""
    culture_advocate: str = ""
    culture_skeptic: str = ""
    trajectory_advocate: str = ""
    trajectory_skeptic: str = ""
    impact_advocate: str = ""
    impact_skeptic: str = ""

class CommitteeVerdictSchema(BaseModel):
    committee_name: str = ""
    pros: str = ""
    cons: str = ""
    score: int = 5
    confidence_pct: int = 70
    hire_label: str = ""
    summary: str = ""
    top_objection: str = ""
    mitigation: str = ""
    cv_gaps: list[str] = Field(default_factory=list)

class CritiqueResultSchema(BaseModel):
    alignment_score: int = 5
    fidelity_score: int = 5
    positioning_score: int = 5
    fabricated_claims: list[str] = Field(default_factory=list)
    revision_instructions: str = ""

class QAPair(BaseModel):
    question: str
    answer: str

class ApplicationAnswers(BaseModel):
    qa_pairs: list[QAPair] = Field(default_factory=list)
