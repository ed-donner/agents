from typing import Annotated, Any, List
from uuid import uuid4

from langgraph.graph import add_messages
from pydantic import BaseModel, Field


class JobPosting(BaseModel):
    """Job posting"""

    id: str = Field(default_factory=lambda: str(uuid4()))
    title: str
    company_name: str
    company_url: str
    location: str
    salary_range: str
    job_description: str
    job_requirements: str
    technologies_needed: str
    must_have_skills: str
    link_to_job_posting: str
    job_posting_date: str


class JobPostingList(BaseModel):
    """List of job postings"""

    job_postings: list[JobPosting]


class Evaluation(BaseModel):
    """Evaluation of the job posting"""

    is_acceptable: bool
    feedback: str
    job_posting_id: str


class EvaluationList(BaseModel):
    """List of evaluations"""

    evaluations: list[Evaluation]


class Notification(BaseModel):
    """Notification of the job postings that are acceptable"""

    job_posting: JobPosting
    feedback: str


class NotificationList(BaseModel):
    """List of notifications"""

    notifications: list[Notification]


class State(BaseModel):
    messages: Annotated[List[Any], add_messages]
    job_posting_url: str
    job_postings: JobPostingList
    evaluations: EvaluationList
    notifications: NotificationList
