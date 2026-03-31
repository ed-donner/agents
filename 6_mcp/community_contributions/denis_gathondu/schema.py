from pydantic import BaseModel


class JobPost(BaseModel):
    """Job posting"""

    id: int
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
    job_post_date: str


class JobPosts(BaseModel):
    """List of job postings"""

    job_posts: list[JobPost]


class Evaluation(BaseModel):
    """Evaluation of the job posting"""

    id: int | None = None
    is_acceptable: bool
    feedback: str
    job_post_id: int


class Evaluations(BaseModel):
    """List of evaluations"""

    evaluations: list[Evaluation]


class Notification(BaseModel):
    """Notification record for a sent job application email"""

    id: int | None = None
    evaluation_id: int
    notified: bool = False


class Notifications(BaseModel):
    """List of notifications"""

    notifications: list[Notification]
