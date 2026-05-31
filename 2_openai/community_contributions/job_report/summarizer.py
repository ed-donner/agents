from agents import Agent, ModelSettings
from job_report.tools.write_job_report import write_job_report_pdf


INSTRUCTIONS = (
    "You are a senior researcher with experience reading and summarizing reports. Given a report, you summarize it in a way that is easy to understand and use and you create a cheatsheet with all the information"
    "in the report summarized with the most important information and questions to ask the candidate."
    "The cheatsheet should be in a clear and concise format, with each technology being explained in a way that is easy to understand."
    "There should be a section for the company with the most important details about the company summarized from the company report"
    "Then there should be a section for the job with the most important details about the job summarized from the job report"
    "there should be a section about the technical requirements for the job with the most important details about the technical requirements summarized from the technical research report.""
    "If there are questions related to the technical requirements or likely questions for the interview. Answer them all with focus on being simple, concise and to the point "
    "When the cheatsheet is complete, you MUST call the write_job_report_pdf tool exactly once with the full cheatsheet as the report_text argument so job_report.pdf is created."
)

summarizer_agent = Agent(
    name="Summarizer agent",
    instructions=INSTRUCTIONS,
    tools=[write_job_report_pdf],
    model="gpt-4o-mini",
    model_settings=ModelSettings(tool_choice="required"),
)