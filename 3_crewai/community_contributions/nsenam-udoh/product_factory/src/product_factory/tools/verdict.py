from pydantic import BaseModel, Field


class QualityVerdict(BaseModel):
    passed: bool
    fixes: list[str] = Field(default_factory=list)
    evidence: list[str] = Field(default_factory=list)
