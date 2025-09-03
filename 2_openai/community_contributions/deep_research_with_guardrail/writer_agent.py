from pydantic import BaseModel, Field
from agents import Agent, output_guardrail, GuardrailFunctionOutput,OutputGuardrailTripwireTriggered, RunContextWrapper,Runner
#from guardrail_agent import guardrail_agent, guardrail_output_length

INSTRUCTIONS = (
    "You are a senior researcher tasked with writing a cohesive report for a research query. "
    "You will be provided with the original query, and some initial research done by a research assistant.\n"
    "You should first come up with an outline for the report that describes the structure and "
    "flow of the report. Then, generate the report and return that as your final output.\n"
    "The final output should be in markdown format, and it should be lengthy and detailed. Aim "
    "for 5-10 pages of content."
)


class ReportData(BaseModel):

    guard_rail_output: str = Field(description="guardrail output")
    guard_rail_tripped: bool = Field(description="guard_rail tripped")
    short_summary: str = Field(description="A short 2-3 sentence summary of the findings.")

    markdown_report: str = Field(description="The final report")

    follow_up_questions: list[str] = Field(description="Suggested topics to research further")

class CheckOutputLength(BaseModel):
    is_report_too_long: bool
    reason: str

guardrail_agent = Agent( 
    name="Check maximum length",
    instructions="Check if output longer than 999 words",
    output_type=CheckOutputLength,
    model="gpt-4o-mini"
)

@output_guardrail
async def guardrail_output_length(ctx: RunContextWrapper, agent: Agent, output: ReportData) -> GuardrailFunctionOutput:
    result = await Runner.run(guardrail_agent, output.markdown_report, context=ctx.context)
    print(result.final_output.reason)
    print(result.final_output.is_report_too_long)
    output.guard_rail_output=result.final_output.reason
    output.guard_rail_tripped=result.final_output.is_report_too_long
    return GuardrailFunctionOutput(output_info={"output_too_long": result.final_output.reason},tripwire_triggered=False)


writer_agent = Agent(
    name="WriterAgent",
    instructions=INSTRUCTIONS,
    model="gpt-4o-mini",
    output_type=ReportData,
    output_guardrails=[guardrail_output_length]
)