import os

import sendgrid
from agents import Agent, WebSearchTool, ModelSettings, function_tool
from sendgrid import Email, To, Content, Mail

from deep_research_models import WebSearchPlan, ReportData

GPT_MODEL = "gpt-4.0-mini"
HOW_MANY_SEARCHES = 5
SENDER = "remo@codesync.ug"
RECIPIENT = "remo.samuelpaul@gmail.com"

search_agent_instructions = (
    "You are a research assistant. Given a search term, you search the web for that term and "
    "produce a concise summary of the results. The summary must 2-3 paragraphs and less than 300 "
    "words. Capture the main points. Write brief succinctly, no need to have complete sentences or good "
    "grammar. This will be consumed by someone synthesizing a report, so its vital you capture the "
    "essence and ignore any fluff. Do not include any additional commentary other than the summary itself."
)

email_agent_instructions = """You are able to send a nicely formatted HTML email based on a detailed report.
You will be provided with a detailed report. You should use your tool to send one email, providing the 
report converted into clean, well presented HTML with an appropriate subject line."""

writer_agent_instructions = (
    "You are a senior researcher tasked with writing a cohesive report for a research query. "
    "You will be provided with the original query, and some initial research done by a research assistant.\n"
    "You should first come up with an outline for the report that describes the structure and "
    "flow of the report. Then, generate the report and return that as your final output.\n"
    "The final output should be in markdown format, and it should be lengthy and detailed. Aim "
    "for 5-10 pages of content, at least 1000 words."
)

planner_agent_instructions = f"""You are a helpful research assistant. Given a query, 
        come up with a set of web searches to perform to best answer the query. 
        Output {HOW_MANY_SEARCHES} terms to query for.
        """


@function_tool
def send_email(subject: str, html_body: str, sender=SENDER, recipient=RECIPIENT) -> str:
    sg = sendgrid.SendGridAPIClient(api_key=os.environ.get("SENDGRID_API_KEY"))
    from_email = Email(sender)
    to_email = To(recipient)
    content = Content("text/html", html_body)
    mail = Mail(from_email, to_email, subject, content).get()
    response = sg.client.mail.send.post(request_body=mail)
    print("Email response", response.status_code)
    return "success"


email_agent = Agent(
    name="Email agent",
    instructions=email_agent_instructions,
    tools=[send_email],
    model=GPT_MODEL,
)

planner_agent = Agent(
    name="PlannerAgent",
    instructions=planner_agent_instructions,
    model=GPT_MODEL,
    output_type=WebSearchPlan,
)

search_agent = Agent(
    name="Search agent",
    instructions=search_agent_instructions,
    tools=[WebSearchTool(search_context_size="low")],
    model=GPT_MODEL,
    model_settings=ModelSettings(tool_choice="required"),
)

writer_agent = Agent(
    name="WriterAgent",
    instructions=writer_agent_instructions,
    model=GPT_MODEL,
    output_type=ReportData,
)
