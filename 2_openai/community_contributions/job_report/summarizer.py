from agents import Agent, ModelSettings
from 

INSTRUCTIONS = (
    "You are a senior manager with experience reading and summarizing reports. Given a report, you summarize it in a way that is easy to understand and use and you create a cheatsheet with all the information"
    "in the report summarized with the most important information and questions to ask the candidate."
    "The cheatsheet should be in a clear and concise format, with each technology being explained in a way that is easy to understand."
    "There should be a section for the company with the most important details about the company summarized from the company report"
    "Then there should be a section for the job with the most important details about the job summarized from the job report"
    "there should be a section about the technical requirements for the job with the most important details about the technical requirements summarized from the technical research report"
    "Write this report in a pdf with a tool that you have been given to do so"
)

summarizer_agent = Agent(
    name="Summarizer agent",
    instructions=INSTRUCTIONS,
    tools=[write_job_report_pdf],
    model="gpt-4o-mini",
    model_settings=ModelSettings(tool_choice="required"),
)