"""
Hunt Manager - Orchestrates the complete job hunting workflow.

Coordinates all agents and provides observability via Langfuse.
"""

import asyncio
import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field

from src.config import get_settings
from src.agent_workers.resume_parser import parse_resume, ParsedResume
from src.agent_workers.profile_builder import build_profile, ProfileBuildResult
from src.agent_workers.job_search import search_jobs_direct, JobSearchResult
from src.agent_workers.job_matcher import match_jobs, match_jobs_fast, MatchingResult


class HuntResult(BaseModel):
    """Result of a complete job hunting session."""
    session_id: str = Field(description="Unique session identifier")
    profile_id: Optional[int] = Field(default=None, description="Profile ID if created/found")
    jobs_found: int = Field(default=0, description="Total jobs found from boards")
    jobs_matched: int = Field(default=0, description="Jobs matching 90%+ criteria")
    duration_seconds: float = Field(default=0.0, description="Total execution time")
    status: str = Field(default="pending", description="Session status")
    error: Optional[str] = Field(default=None, description="Error message if failed")
    trace_url: Optional[str] = Field(default=None, description="Langfuse trace URL")


class HuntManager:
    """
    Orchestrates the job hunting workflow.
    
    Workflow:
    1. Parse resume (extract text, structure data)
    2. Build/update profile in database
    3. Search job boards with profile keywords
    4. Match jobs against profile (90%+ threshold)
    5. Save matching jobs to database
    """
    
    def __init__(self):
        self.settings = get_settings()
        self._langfuse = None
        self._init_langfuse()
    
    def _init_langfuse(self):
        """Initialize Langfuse client if configured."""
        if not self.settings.langfuse_enabled:
            return
        
        try:
            from langfuse import Langfuse
            self._langfuse = Langfuse(
                public_key=self.settings.langfuse_public_key,
                secret_key=self.settings.langfuse_secret_key,
                host=self.settings.langfuse_host,
            )
        except ImportError:
            pass
        except Exception:
            pass
    
    def _create_trace(self, session_id: str, name: str = "job_hunt"):
        """Create a Langfuse trace for the session."""
        if not self._langfuse:
            return None
        
        try:
            return self._langfuse.trace(
                id=session_id,
                name=name,
                metadata={"version": "1.0"},
            )
        except Exception:
            return None
    
    def _log_span(self, trace, name: str, input_data: dict, output_data: dict, duration_ms: float):
        """Log a span to Langfuse."""
        if not trace:
            return
        
        try:
            trace.span(
                name=name,
                input=input_data,
                output=output_data,
                metadata={"duration_ms": duration_ms},
            )
        except Exception:
            pass
    
    async def hunt(self, resume_path: str, use_agent_matching: bool = False) -> HuntResult:
        """
        Execute the complete job hunting workflow.
        
        Args:
            resume_path: Path to the resume file (PDF or DOCX)
            use_agent_matching: If True, use LLM agent for matching; otherwise fast rule-based
            
        Returns:
            HuntResult with session details
        """
        session_id = str(uuid.uuid4())
        start_time = datetime.now()
        trace = self._create_trace(session_id)
        
        result = HuntResult(
            session_id=session_id,
            status="running",
        )
        
        try:
            parsed_resume = await self._parse_resume(resume_path, trace)
            
            profile_result = await self._build_profile(parsed_resume, trace)
            result.profile_id = profile_result.profile_id
            
            if not result.profile_id:
                result.status = "failed"
                result.error = "Failed to create profile"
                return result
            
            keywords = self._extract_search_keywords(parsed_resume)
            
            search_result = await self._search_jobs(keywords, trace)
            result.jobs_found = search_result.total_found
            
            if search_result.total_found == 0:
                result.status = "completed"
                return result
            
            if use_agent_matching:
                matching_result = await self._match_jobs_agent(
                    result.profile_id, search_result.jobs, trace
                )
                result.jobs_matched = matching_result.total_matched
            else:
                matched_jobs = self._match_jobs_fast(
                    result.profile_id, search_result.jobs, trace
                )
                result.jobs_matched = len(matched_jobs)
                
                await self._save_matched_jobs(result.profile_id, matched_jobs, trace)
            
            result.status = "completed"
            
        except Exception as e:
            result.status = "failed"
            result.error = str(e)
        
        finally:
            end_time = datetime.now()
            result.duration_seconds = (end_time - start_time).total_seconds()
            
            if trace and self._langfuse:
                try:
                    trace.update(
                        output={
                            "status": result.status,
                            "jobs_found": result.jobs_found,
                            "jobs_matched": result.jobs_matched,
                        }
                    )
                    self._langfuse.flush()
                    result.trace_url = f"{self.settings.langfuse_host}/trace/{session_id}"
                except Exception:
                    pass
        
        return result
    
    async def _parse_resume(self, resume_path: str, trace) -> ParsedResume:
        """Parse resume and extract structured data."""
        start = datetime.now()
        
        parsed = await parse_resume(resume_path)
        
        duration_ms = (datetime.now() - start).total_seconds() * 1000
        self._log_span(
            trace, "parse_resume",
            {"file_path": resume_path},
            {"name": parsed.name, "skills_count": len(parsed.skills)},
            duration_ms,
        )
        
        return parsed
    
    async def _build_profile(self, parsed_resume: ParsedResume, trace) -> ProfileBuildResult:
        """Build or update profile from parsed resume."""
        start = datetime.now()
        
        result = await build_profile(parsed_resume)
        
        duration_ms = (datetime.now() - start).total_seconds() * 1000
        self._log_span(
            trace, "build_profile",
            {"name": parsed_resume.name, "email": parsed_resume.email},
            {"profile_id": result.profile_id, "is_new": result.is_new},
            duration_ms,
        )
        
        return result
    
    def _extract_search_keywords(self, parsed_resume: ParsedResume) -> list[str]:
        """Extract keywords from parsed resume for job search."""
        keywords = set()
        
        for skill in parsed_resume.skills:
            keywords.add(skill.name.lower())
        
        keywords.update(k.lower() for k in parsed_resume.keywords)
        
        for exp in parsed_resume.experience:
            title_words = exp.title.lower().split()
            for word in title_words:
                if len(word) > 3 and word not in {"with", "for", "and", "the"}:
                    keywords.add(word)
        
        return list(keywords)[:10]
    
    async def _search_jobs(self, keywords: list[str], trace) -> JobSearchResult:
        """Search all job boards."""
        start = datetime.now()
        
        result = await search_jobs_direct(keywords)
        
        duration_ms = (datetime.now() - start).total_seconds() * 1000
        self._log_span(
            trace, "search_jobs",
            {"keywords": keywords},
            {
                "total_found": result.total_found,
                "boards_searched": result.boards_searched,
                "errors": result.errors,
            },
            duration_ms,
        )
        
        return result
    
    async def _match_jobs_agent(
        self, profile_id: int, jobs: list[dict], trace
    ) -> MatchingResult:
        """Match jobs using LLM agent."""
        start = datetime.now()
        
        result = await match_jobs(profile_id, jobs)
        
        duration_ms = (datetime.now() - start).total_seconds() * 1000
        self._log_span(
            trace, "match_jobs_agent",
            {"profile_id": profile_id, "jobs_count": len(jobs)},
            {"matched": result.total_matched, "evaluated": result.total_evaluated},
            duration_ms,
        )
        
        return result
    
    def _match_jobs_fast(
        self, profile_id: int, jobs: list[dict], trace
    ) -> list[dict]:
        """Match jobs using fast rule-based scoring."""
        start = datetime.now()
        
        matched = match_jobs_fast(profile_id, jobs, threshold=self.settings.match_threshold)
        
        duration_ms = (datetime.now() - start).total_seconds() * 1000
        self._log_span(
            trace, "match_jobs_fast",
            {"profile_id": profile_id, "jobs_count": len(jobs)},
            {"matched_count": len(matched)},
            duration_ms,
        )
        
        return matched
    
    async def _save_matched_jobs(
        self, profile_id: int, matched_jobs: list[dict], trace
    ):
        """Save matched jobs to database."""
        from src.db.repository import JobRepository
        from src.schemas.job import JobCreate
        
        SessionFactory = _get_session_factory()
        session = SessionFactory()
        job_repo = JobRepository(session)
        
        saved_count = 0
        for job in matched_jobs:
            if job_repo.exists(job.get("external_id", ""), job.get("source", ""), profile_id):
                continue
            
            try:
                job_data = JobCreate(
                    profile_id=profile_id,
                    external_id=job.get("external_id", str(uuid.uuid4())),
                    source=job.get("source", "other"),
                    title=job.get("title", "Unknown"),
                    company=job.get("company", "Unknown"),
                    description=job.get("description", "")[:2000],
                    url=job.get("url", ""),
                    location=job.get("location"),
                    salary_range=job.get("salary_range"),
                    match_score=job.get("match_score", 0.9),
                    required_skills=job.get("required_skills", []),
                    match_details=[job.get("match_details", {})],
                )
                job_repo.create(job_data)
                saved_count += 1
            except Exception:
                continue
        
        self._log_span(
            trace, "save_matched_jobs",
            {"profile_id": profile_id, "jobs_to_save": len(matched_jobs)},
            {"saved_count": saved_count},
            0,
        )
    
    async def search_only(self, profile_id: int, keywords: list[str]) -> HuntResult:
        """
        Run job search and matching for an existing profile.
        
        Args:
            profile_id: Existing profile ID
            keywords: Keywords to search for
            
        Returns:
            HuntResult with search results
        """
        session_id = str(uuid.uuid4())
        start_time = datetime.now()
        trace = self._create_trace(session_id, "job_search")
        
        result = HuntResult(
            session_id=session_id,
            profile_id=profile_id,
            status="running",
        )
        
        try:
            search_result = await self._search_jobs(keywords, trace)
            result.jobs_found = search_result.total_found
            
            if search_result.total_found > 0:
                matched_jobs = self._match_jobs_fast(profile_id, search_result.jobs, trace)
                result.jobs_matched = len(matched_jobs)
                await self._save_matched_jobs(profile_id, matched_jobs, trace)
            
            result.status = "completed"
            
        except Exception as e:
            result.status = "failed"
            result.error = str(e)
        
        finally:
            end_time = datetime.now()
            result.duration_seconds = (end_time - start_time).total_seconds()
            
            if self._langfuse:
                try:
                    self._langfuse.flush()
                    result.trace_url = f"{self.settings.langfuse_host}/trace/{session_id}"
                except Exception:
                    pass
        
        return result


def _get_session_factory():
    """Get the database session factory."""
    from src.db.models import init_database
    settings = get_settings()
    return init_database(settings.database_url)
