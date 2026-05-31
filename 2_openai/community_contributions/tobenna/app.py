import asyncio
from typing import Optional

import gradio as gr
from dotenv import load_dotenv
from pydantic import BaseModel, Field

from agents import Agent, Runner, WebSearchTool, trace

load_dotenv(override=True)

INSTRUCTIONS1 = """
You are a CV reviewer. You are given a CV and you need to review it and extract information that
is relevant and will be used to search the internet for matching jobs. This will be used by a job
scout to find matching jobs on the internet.
"""

INSTRUCTIONS2 = """
You are a job scout. Given a candidate's professional description, you are required to search the internet for matching jobs.
Return at most 10 matching jobs.
"""

INSTRUCTIONS3 = """
You are a recruiter. You are given a candidate's resume and you need to review it and extract information that
is relevant and will be used to search the internet for matching jobs. You also return a remark on whether
you were able to find matching jobs or not; or on whether the resume contained enough information or not.
Whatever the final result is, it must be in markdown format. Do not include any code blocks. It must be a
readable markdown as-is.
"""

INSTRUCTIONS4 = """
You are a formatter. You are given a list of jobs and you need to format them into markdown. Each job should be in its own section.
"""


class Job(BaseModel):
    title: str = Field(description="The title of the job")
    company: str = Field(description="The company of the job")
    location: Optional[str] = Field(description="The location of the job")
    description: Optional[str] = Field(description="The description of the job")
    url: str = Field(description="The url of the job")


class JobSearch(BaseModel):
    jobs: list[Job] = Field(description="The matching jobs on the internet")


class CVReview(BaseModel):
    technical_skills: list[str] = Field(
        description="The technical skills of the candidate"
    )
    soft_skills: list[str] = Field(description="The soft skills of the candidate")
    experience: int = Field(description="The experience of the candidate in years")
    has_bachelors_degree: bool = Field(
        description="Whether the candidate has a bachelors degree"
    )
    has_masters_degree: bool = Field(
        description="Whether the candidate has a masters degree"
    )
    possible_positions: list[str] = Field(
        description="The possible positions the candidate is eligible for"
    )
    seniority_level: str = Field(
        description="The seniority level of the candidate based on the experience and the biggest achievement"
    )


class Recruiter(BaseModel):
    remark: str = Field(
        description="A remark on whether you were able to find matching jobs or not; or on whether the resume contained enough information or not"
    )
    jobs: list[Job] = Field(description="The matching jobs on the internet")


job_scout_agent = Agent(
    name="Job Scout",
    instructions=INSTRUCTIONS2,
    model="gpt-4o-mini",
    output_type=JobSearch,
    tools=[
        WebSearchTool(
            search_context_size="low",
        )
    ],
)

cv_reviewer_agent = Agent(
    name="CV Reviewer",
    instructions=INSTRUCTIONS1,
    model="gpt-4o-mini",
    output_type=CVReview,
)

formatter_agent = Agent(
    name="Formatter",
    instructions=INSTRUCTIONS4,
    model="gpt-4o-mini",
    output_type=str,
    handoff_description="Format the list of jobs into markdown. Each job should be in its own section. The markdown should be immediately usable in a markdown viewer and not inside a code block.",
)

cv_review_agent_tool = cv_reviewer_agent.as_tool(
    tool_name="cv_reviewer",
    tool_description="Review a CV and extract information that is relevant and will be used to search the internet for matching jobs",
)

job_scout_agent_tool = job_scout_agent.as_tool(
    tool_name="job_scout",
    tool_description="Search the internet for matching jobs",
)

recruiter_agent = Agent(
    name="Recruiter",
    instructions=INSTRUCTIONS3,
    model="gpt-4o-mini",
    output_type=Recruiter,
    tools=[cv_review_agent_tool, job_scout_agent_tool],
    handoffs=[formatter_agent],
)


async def find_matching_jobs(cv: str):
    with trace("Recruiter"):
        result = await Runner.run(
            recruiter_agent,
            f"Given the candidate's CV: {cv}:\n\n Review it and extract relevant information that will be \
          used to search the internet for matching jobs.\n\n Format the jobs returned into markdown. Each job should be in its own section.\
             THE SEARCH RESULT MUST BE FORMATTED INTO MARKDOWN. DO NOT INCLUDE ANY CODE BLOCKS.",
        )
        return result.final_output


def start():
    with gr.Blocks(theme=gr.themes.Default()) as ui:
        with gr.Column():
            gr.Markdown("# Inginia's Job Agency")
        with gr.Row():
            cv = gr.Textbox(label="CV", lines=20)
            review = gr.Markdown(label="Matching Jobs", height=400)
        with gr.Column():
            review_button = gr.Button(variant="primary", value="Find Matching Jobs")
        review_button.click(find_matching_jobs, inputs=[cv], outputs=[review])
    ui.launch(inbrowser=True)


if __name__ == "__main__":
    start()
