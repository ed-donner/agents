from pydantic import BaseModel
from typing import List

class AnalyzeProcessInput(BaseModel):
    process_steps: List[str]

class AnalyzeProcessOutput(BaseModel):
    structured_steps: List[str]
    summary: str

class StandardStep(BaseModel):
    step: str
    priority: str  # high / medium / low

class DetectGapsInput(BaseModel):
    domain: str
    process_name: str
    process_steps: List[str]

class DetectGapsOutput(BaseModel):
    gaps: List[StandardStep]

class Recommendation(BaseModel):
    action: str
    reason: str
    impact: str

class GenerateRecommendationsInput(BaseModel):
    gaps: List[StandardStep]

class GenerateRecommendationsOutput(BaseModel):
    recommendations: List[Recommendation]

class RedesignProcessInput(BaseModel):
    original_steps: List[str]
    recommendations: List[Recommendation]

class RedesignProcessOutput(BaseModel):
    improved_process: List[str]