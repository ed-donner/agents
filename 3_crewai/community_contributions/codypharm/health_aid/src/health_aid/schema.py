from pydantic import BaseModel
from typing import List, Optional

class HealthMetrics(BaseModel):
    blood_pressure: str        
    glucose_mg_dl: float
    bmi: float
    cholesterol_mg_dl: float
    age: int
    flagged: List[str]         

class RiskReport(BaseModel):
    risks: List[str]
    severity: str              
    requires_intervention: bool

class DietPlan(BaseModel):
    recommendations: List[str]
    foods_to_avoid: List[str]
    lifestyle_tips: List[str]