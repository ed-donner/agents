"""Pydantic models for structured agent outputs."""

from pydantic import BaseModel, Field


class JobRequirements(BaseModel):
    """Structured extraction from a job description."""

    role_title: str = Field(description="Job title or closest match if unstated.")
    company_or_context: str = Field(
        description="Company name or context (e.g. industry) if mentioned; else empty string."
    )
    must_have_skills: list[str] = Field(
        description="Must-have skills, tools, or qualifications."
    )
    nice_to_have_skills: list[str] = Field(
        description="Nice-to-have or bonus items; empty list if none."
    )
    key_responsibilities: list[str] = Field(
        description="Main responsibilities as short bullets."
    )
    keywords_for_ats: list[str] = Field(
        description="Keywords to mirror naturally in materials (tech stack, domains)."
    )
    seniority_level: str = Field(
        description="Inferred seniority: e.g. intern, junior, mid, senior, lead, principal."
    )


class SkillMappingRow(BaseModel):
    requirement: str = Field(description="Requirement or theme from the JD.")
    resume_evidence: str = Field(
        description="Concrete evidence from the candidate resume (quote or paraphrase closely)."
    )
    confidence: str = Field(
        description="high, medium, or low — how well the resume supports this requirement."
    )


class SkillMapping(BaseModel):
    rows: list[SkillMappingRow] = Field(
        description="Rows linking JD themes to resume evidence; cover the top must-haves."
    )


class TailoredCoverDraft(BaseModel):
    """Single cover letter opening section (2–4 sentences) tailored to the JD and resume."""

    paragraph: str = Field(
        description="Opening paragraphs only; no addresses or signature; professional tone for body text."
    )


class PickerChoice(BaseModel):
    chosen_cover: str = Field(description="The selected cover opening text only, verbatim from options.")
    one_line_rationale: str = Field(description="Why this version is strongest for the role.")
