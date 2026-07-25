from pydantic import BaseModel


class LanguageDetection(BaseModel):
    language: str
    confidence: float


class EmailDraft(BaseModel):
    language: str
    body: str
    model_used: str


class EmailScore(BaseModel):
    clarity: int
    persuasiveness: int
    professionalism: int
    cta_strength: int

    @property
    def overall(self) -> float:
        return (self.clarity + self.persuasiveness + self.professionalism + self.cta_strength) / 4


class EmailEvaluation(BaseModel):
    language: str
    scores: EmailScore
    brief_comment: str


class JudgeOutput(BaseModel):
    evaluations: list[EmailEvaluation]
    winner_language: str
    reasoning: str
    winner_body: str
