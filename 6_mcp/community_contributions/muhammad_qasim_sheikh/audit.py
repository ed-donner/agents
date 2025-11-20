from dataclasses import dataclass, asdict
from typing import Dict, Any


@dataclass
class AuditResult:
    readability: Dict[str, Any]
    seo: Dict[str, Any]
    tone: Dict[str, Any]
    plagiarism: Dict[str, Any]
    overall_score: float
    summary: str

    def to_dict(self):
        return asdict(self)


def grade_from_scores(score: float) -> str:
    if score >= 85:
        return "Excellent"
    elif score >= 70:
        return "Good"
    elif score >= 50:
        return "Fair"
    else:
        return "Needs Improvement"
