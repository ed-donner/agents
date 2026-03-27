from typing import Any

from applicant import Applicant
from mcp.server.fastmcp import FastMCP
from schema import Evaluation, JobPost, JobPosts

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


@mcp.tool()
def save_evaluation(name: str, evaluation: Evaluation):
    """
    Save an evaluation of a job post to the database.
    """
    return Applicant.get(name).save_evaluation(evaluation)


@mcp.tool()
def read_evaluation(name: str, job_post_id: int) -> Evaluation:
    """
    Read an evaluation for a job post from the database.
    """
    return Applicant.get(name).get_evaluation(job_post_id)


if __name__ == "__main__":
    mcp.run(transport="sse")
