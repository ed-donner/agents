from typing import Any

from applicant import Applicant
from mcp.server.fastmcp import FastMCP
from schema import JobPost, JobPosts

mcp: FastMCP[Any] = FastMCP("applicant_server")


@mcp.tool()
def save_job_post(name: str, job_post: JobPost):
    """
    Save the job posts to the database.
    """
    return Applicant.get(name).save_job_post(job_post)


@mcp.tool()
def read_job_post(name: str, job_post_id: int) -> JobPost:
    """
    Read a job post from the database.
    """
    return Applicant.get(name).read_job_post(job_post_id)


@mcp.resource("applicant://{name}/job_posts")
def list_job_posts(name: str) -> JobPosts:
    """
    List the job posts from the database.
    """
    return Applicant.get(name).list_job_posts()


if __name__ == "__main__":
    mcp.run(transport="sse")
