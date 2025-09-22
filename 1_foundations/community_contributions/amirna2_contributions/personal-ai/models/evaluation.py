from pydantic import BaseModel


class Evaluation(BaseModel):
    """Evaluation result for a response."""
    is_acceptable: bool
    feedback: str
