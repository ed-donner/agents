from pydantic import BaseModel, Field
from agents import Agent, Runner

INSTRUCTION = '''
You are a senior researcher tasked with writing a cohesive report for a research query.
You will be given the original research query and some initial research done by a research assistant.
You should first come up with an outline for the report that describes the structure and flow of the report.
Then, genrate the report and return that as your final answer. The report should be well-structured, and clear, and should effectively communicate the findings of the research.
The final output should be in markdown format, and it should be lengthy and detailed. Aim for 5-10 pages of content, at least 1000 words.
'''


class ReportData(BaseModel):
    short_summary: str = Field(description="A short 2-3 sentence summary of the research findings.")
    markdown_report: str = Field(description="The full report in markdown format.")
    follow_up_questions: list[str] = Field(description='Suggested topics for further research based on the findings of the report.')


class WriterAgent:
    def __init__(self):
        self.writer_agent = Agent(
            name="Writer Agent",
            instructions=INSTRUCTION,
            model="gpt-4o-mini",
            output_type=ReportData,
        )

    async def run(self, summary) -> ReportData:
        ''' Write a comprehensive report based on the research query and the research summary provided by the search agent. '''
        print('Thinking about the report...')
        report_data = await Runner.run(
            self.writer_agent, summary
        )
        return report_data.final_output_as(ReportData)
