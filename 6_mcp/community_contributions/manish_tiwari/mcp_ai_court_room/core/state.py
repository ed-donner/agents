"""Pydantic models for courtroom debate state."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, field_validator


class CaseBrief(BaseModel):
    case_title: str = Field(description="Title of the legal matter")
    summary: str = Field(description="Factual summary")
    legal_issue: str = Field(description="Core legal question")
    plaintiff: str = Field(description="Party asserting a claim or interest")
    defendant: str = Field(description="Party defending or opposing")


class DebateTurn(BaseModel):
    round_num: int
    role: Literal["pro", "against", "judge"]
    content: str


class Judgement(BaseModel):
    reasoning: str
    winner: Literal["pro", "against", "split"]
    judgement: str

    @field_validator("winner", mode="before")
    @classmethod
    def normalize_winner(cls, v: object) -> str:
        if not isinstance(v, str):
            return "split"
        s = v.strip().lower()
        if s in ("pro", "plaintiff", "claimant", "petitioner", "for"):
            return "pro"
        if s in ("against", "defense", "defendant", "respondent", "con"):
            return "against"
        if s in ("split", "tie", "draw", "partial"):
            return "split"
        return "split"


class DebateState(BaseModel):
    case: CaseBrief | None = None
    turns: list[DebateTurn] = Field(default_factory=list)
    judge_comments: list[str] = Field(default_factory=list)
    final: Judgement | None = None
