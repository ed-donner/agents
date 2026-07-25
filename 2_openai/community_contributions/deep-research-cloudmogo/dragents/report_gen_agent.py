from agents import Agent 

from models.models import ReportData

REPORT_WRITER_INSTRUCTIONS = (
    "You are a senrior researcher tasked with writting w cohesive report for a research query. "
    "You will b provided with the original query, and some initial resarch done by a search assisstant. \n"
    "You should first come with an outline for the report that describes the structure and "
    "flow of the report. Then generate the report and return that as your final output. \n"
    "The final output should be in markdown format, and it should be leanghty, and detailed. Aim "
    "for 5-10 page of content, at least 1000 words."
)

report_writer_agent = Agent(
    name = "Report Writer Agent",
    instructions=REPORT_WRITER_INSTRUCTIONS,
    model = "gpt-4o-mini",
    output_type=ReportData,

)