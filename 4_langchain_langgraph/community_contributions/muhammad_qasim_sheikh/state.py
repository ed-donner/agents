from pydantic import BaseModel
from typing import List, Optional

class ResearchState(BaseModel):
    user_query: str

    clarifying_questions: Optional[List[str]] = None
    clarifying_answers: Optional[List[str]] = None
    full_context: Optional[str] = None

    topics: Optional[List[str]] = None

    feedback: Optional[str] = None
    score: Optional[float] = None
    is_acceptable: Optional[bool] = None
    retry_count: int = 0          
    best_topics: Optional[List[str]] = None
    best_score: Optional[float] = None

    selected_topic: Optional[str] = None
    report: Optional[str] = None
    report_feedback: Optional[str] = None
    report_score: Optional[float] = None
    report_is_acceptable: Optional[bool] = None
    report_retry_count: int = 0

    best_report: Optional[str] = None
    best_report_score: Optional[float] = None
    best_report_feedback: Optional[str] = None

    research_snippets: Optional[List[str]] = None

    filename: Optional[str] = None
    report_html: Optional[str] = None
    
    final_status: Optional[str] = None