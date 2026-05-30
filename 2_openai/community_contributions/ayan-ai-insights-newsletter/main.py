from dotenv import load_dotenv
from agents import Runner, trace
import asyncio
from utils import send_mail, prepare_newsletter_html
import os

load_dotenv(override=True)

from research_scout_agent import research_agent
from trend_cluster_agent import trend_cluster_agent
from editorial_prioritizer_agent import editorial_prioritizer_agent
from newsletter_writer_agent import newsletter_writer_agent


async def main() -> None:
    print("Starting Agentic Workflow...")
    with trace("AI Newsletter Agentic Workflow"):
        result = await Runner.run(research_agent, "Do the research for the newsletter")
        research_content = result.final_output

        prompt = "Cluster the following research content into meaningful themes: \n\n" + str(research_content.model_dump_json())
        result = await Runner.run(trend_cluster_agent, prompt)
        clusters = result.final_output

        prompt = "Here are the clusters: \n\n" + str(clusters.model_dump_json())
        result = await Runner.run(editorial_prioritizer_agent, prompt)
        editorial_priorities = result.final_output

        prompt = "Write the newsletter with the following information: \n\n"
        prompt += "Here is the Research content: \n\n" + str(research_content.model_dump_json())
        prompt += "Here are the clusters: \n\n" + str(clusters.model_dump_json())
        prompt += "Here are the editorial priorities: \n\n" + str(editorial_priorities.model_dump_json())

        result = await Runner.run(newsletter_writer_agent, prompt)
        newsletter_content = result.final_output
    print("Agent Workflow execution ended successfully.")
    full_html = prepare_newsletter_html(newsletter_content)
    from_email = os.environ.get("SENDGRID_FROM_EMAIL")
    to_email = os.environ.get("SENDGRID_TO_EMAIL")
    print("Sending mail from ", from_email, " to ", to_email)
    send_mail(full_html, from_email, to_email)


if __name__ == "__main__":
    asyncio.run(main())
    