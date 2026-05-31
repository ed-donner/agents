from pydantic import BaseModel
from typing import Optional, Literal


class SessionRequest(BaseModel):
    pass


class ChallengeRequest(BaseModel):
    challenge: str


class StateResponse(BaseModel):
    session_id: str
    state: Literal["challenge", "plan", "build", "busy"]
    challenge: Optional[str] = None
    language: Optional[str] = None
    plan: Optional[str] = None
    build_status: Optional[str] = None


class BuildResponse(BaseModel):
    session_id: str
    files_created: list[str]
    files_skipped: list[str] = []
    project_path: str
    status: str
