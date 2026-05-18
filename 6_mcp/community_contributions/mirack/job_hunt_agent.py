
import os
import asyncio
from dotenv import load_dotenv
from openai import AsyncOpenAI
from agents import Agent, Runner, trace
from agents.mcp import MCPServerStdio

load_dotenv(override=True)

from agents import OpenAIChatCompletionsModel

openrouter_client = AsyncOpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.environ.get("API_TOKEN")
)

MODEL = OpenAIChatCompletionsModel(
    model="gpt-4o-mini",
    openai_client=openrouter_client
)

#  CV info (Can be edited) 
MY_CV = """
Name: Nwadiaro Miracle Chukwuma
Role: ML Engineer / AI Engineer
Location: Uyo, Nigeria (open to remote)
Experience: 3+ years

Current: ML Engineer at Safeguardmedia — deepfake detection, computer vision, MLOps
Previous: ML Intern at Start Innovation Hub, Software Dev at DevCareer, Intern at Distrobird

Skills: Python, TensorFlow, PyTorch, HuggingFace, OpenAI API, LangChain, LangGraph,
CrewAI, AutoGen, FastAPI, Docker, Kubernetes, MLflow, GCP, React, Next.js, MongoDB

Education: B.Eng. Electrical Engineering, FUTO (4.20/5.00, Second Class Upper)
Portfolio: mirack.site | GitHub: miracle73
"""


async def main():
    # Connect to MCP server
    mcp_server = MCPServerStdio(
        name="Job Hunt Server",
        params={
            "command": "uv",
            "args": ["run", "job_hunt_server.py"]
        }
    )

    # Create the job hunt agent
    job_agent = Agent(
        name="Job Hunt Assistant",
        instructions=f"""You are a job hunt assistant helping a candidate find and apply for jobs.

Here is the candidate's CV:
{MY_CV}

Your workflow when asked to find jobs:
1. Use search_jobs to find relevant listings
2. For each promising job, use match_cv_to_job to score the fit
3. For strong matches (60%+), use draft_cover_letter to create a draft
4. Use save_application to track everything
5. Give honest advice — don't sugarcoat weak matches

When asked about progress, use list_applications and get_hunt_stats.

Be direct and practical. This person needs a job, not motivational speeches.""",
        mcp_servers=[mcp_server],
        model=MODEL
    )

    async with mcp_server:
        print("Job Hunt Agent ready. Connected to MCP server.\n")
        print("=" * 50)

       
        with trace("Job Search"):
            print("\n--- Searching for ML Engineer roles ---\n")
            result = await Runner.run(
                job_agent,
                "Find ML Engineer jobs in Nigeria or remote. Match each one to my CV and tell me which ones I should apply to. Save the best matches to my tracker."
            )
            print(result.final_output)

        print("\n" + "=" * 50)

      
        with trace("Draft Application"):
            print("\n--- Drafting application for best match ---\n")
            result = await Runner.run(
                job_agent,
                "Draft a cover letter for the job that matched my CV best. Make it specific to my deepfake detection experience and AI engineering skills."
            )
            print(result.final_output)

        print("\n" + "=" * 50)

       
        with trace("Hunt Stats"):
            print("\n--- Job hunt progress ---\n")
            result = await Runner.run(
                job_agent,
                "Show me my job hunt stats and all tracked applications."
            )
            print(result.final_output)


if __name__ == "__main__":
    asyncio.run(main())
