from typing import Literal

from pydantic import BaseModel


class EvaluationFeedback(BaseModel):
    feedback: str
    score: Literal["pass", "needs_improvement", "fail"]
