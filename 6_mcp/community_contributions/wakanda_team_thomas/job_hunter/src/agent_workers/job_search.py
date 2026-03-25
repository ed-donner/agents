"""
Job Search Agent.

Searches multiple job boards for remote positions matching profile keywords.
"""

import asyncio
from typing import Optional
from pydantic import BaseModel, Field

from agents import Agent, function_tool

from src.job_boards import get_all_clients, RemoteOKClient, RemotiveClient, ArbeitnowClient
from src.schemas.job import JobBoardListing


class JobSearchResult(BaseModel):
    """Result of job search operation."""
    total_found: int = Field(description="Total number of jobs found across all boards")
    jobs: list[dict] = Field(default_factory=list, description="List of job listings")
    boards_searched: list[str] = Field(default_factory=list, description="Names of job boards searched")
    errors: list[str] = Field(default_factory=list, description="Any errors encountered during search")


def _search_board_sync(client_class, keywords: list[str]) -> tuple[list[dict], Optional[str]]:
    """Synchronously search a single job board."""
    import asyncio
    
    async def _search():
        async with client_class() as client:
            try:
                jobs = await client.search(keywords)
                return [job.model_dump() for job in jobs], None
            except Exception as e:
                return [], str(e)
    
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(_search())
    finally:
        loop.close()


@function_tool
def search_remoteok(keywords: list[str]) -> str:
    """
    Search RemoteOK for remote job listings.
    
    Args:
        keywords: List of keywords to search for (skills, technologies, job titles)
        
    Returns:
        JSON string with jobs found or error message
    """
    import json
    
    jobs, error = _search_board_sync(RemoteOKClient, keywords)
    
    if error:
        return f"error:{error}"
    
    return json.dumps({"source": "remoteok", "count": len(jobs), "jobs": jobs})


@function_tool
def search_remotive(keywords: list[str]) -> str:
    """
    Search Remotive for remote job listings.
    
    Args:
        keywords: List of keywords to search for (skills, technologies, job titles)
        
    Returns:
        JSON string with jobs found or error message
    """
    import json
    
    jobs, error = _search_board_sync(RemotiveClient, keywords)
    
    if error:
        return f"error:{error}"
    
    return json.dumps({"source": "remotive", "count": len(jobs), "jobs": jobs})


@function_tool
def search_arbeitnow(keywords: list[str]) -> str:
    """
    Search Arbeitnow for remote job listings.
    
    Args:
        keywords: List of keywords to search for (skills, technologies, job titles)
        
    Returns:
        JSON string with jobs found or error message
    """
    import json
    
    jobs, error = _search_board_sync(ArbeitnowClient, keywords)
    
    if error:
        return f"error:{error}"
    
    return json.dumps({"source": "arbeitnow", "count": len(jobs), "jobs": jobs})


SEARCH_INSTRUCTIONS = """You are a job search agent. Your task is to search multiple job boards
for remote positions that match the given keywords.

When searching for jobs:

1. Use all three search tools to maximize coverage:
   - search_remoteok: Popular board for remote tech jobs
   - search_remotive: Curated remote jobs in tech
   - search_arbeitnow: European-focused but worldwide remote jobs

2. Use relevant keywords from the profile:
   - Primary skills (Python, JavaScript, etc.)
   - Job titles (Software Engineer, Data Scientist, etc.)
   - Technologies (AWS, Docker, React, etc.)

3. Combine results from all boards, noting the source of each job

4. Report any errors encountered but continue with other boards

Return a JobSearchResult with:
- total_found: Total jobs found across all boards
- jobs: List of all job listings (include source in each)
- boards_searched: List of boards that were successfully searched
- errors: Any errors encountered

IMPORTANT: Only 100% remote worldwide positions are returned by the search tools.
All jobs returned are already filtered for remote work."""


job_search_agent = Agent(
    name="JobSearchAgent",
    instructions=SEARCH_INSTRUCTIONS,
    model="gpt-4o-mini",
    tools=[
        search_remoteok,
        search_remotive,
        search_arbeitnow,
    ],
    output_type=JobSearchResult,
)


async def search_jobs(keywords: list[str]) -> JobSearchResult:
    """
    Search all job boards for positions matching the given keywords.
    
    Args:
        keywords: List of keywords to search for
        
    Returns:
        JobSearchResult with all found jobs
    """
    from agents import Runner
    
    result = await Runner.run(
        job_search_agent,
        f"Search for remote jobs matching these keywords: {', '.join(keywords)}",
    )
    
    return result.final_output_as(JobSearchResult)


async def search_jobs_direct(keywords: list[str]) -> JobSearchResult:
    """
    Search all job boards directly without using the agent (faster).
    
    Args:
        keywords: List of keywords to search for
        
    Returns:
        JobSearchResult with all found jobs
    """
    all_jobs = []
    boards_searched = []
    errors = []
    
    client_classes = [RemoteOKClient, RemotiveClient, ArbeitnowClient]
    
    def search_one(client_class):
        with client_class() as client:
            try:
                jobs = client.search(keywords)
                return client.source_name, [j.model_dump() for j in jobs], None
            except Exception as e:
                return client.source_name, [], str(e)
    
    loop = asyncio.get_event_loop()
    tasks = [loop.run_in_executor(None, search_one, c) for c in client_classes]
    results = await asyncio.gather(*tasks)
    
    for source, jobs, error in results:
        if error:
            errors.append(f"{source}: {error}")
        else:
            boards_searched.append(source)
            all_jobs.extend(jobs)
    
    return JobSearchResult(
        total_found=len(all_jobs),
        jobs=all_jobs,
        boards_searched=boards_searched,
        errors=errors,
    )
