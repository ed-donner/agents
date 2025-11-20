from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field
from state import ResearchState

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.2)

class ReportResult(BaseModel):
    report: str = Field(description="A structured research report.")

def report_writer_node(state: ResearchState) -> ResearchState:
    print("EXECUTING: WRITER NODE")
    structured_llm = llm.with_structured_output(ReportResult)

    research_summary = "\n\n".join(state.research_snippets or [])

    prompt = f"""
    You are a senior researcher tasked with writing a cohesive, report for a research query.
    You are provided with the following inputs:
    1. Full research context including the original query and clarifications: {state.full_context}
    2. Collection of supporting research data: {research_summary}
    Your task is to generate a comprehensive report in markdown format.

    **CRITICAL REQUIREMENT: The final report MUST BE at least 1000 words.**
    
    This is a non-negotiable requirement. The report will be automatically rejected if it is shorter.
    You must be verbose, detailed, and expand on all points to meet this length.
    - Start with a detailed outline.
    - Write the full report based on that outline.
    - Ensure the report is well-structured, detailed, and comprehensive.
    - Include a "References" section at the end.
    - Do not write "I have generated a 1000-word report." Just write the report.
    """

    if state.report_feedback and not state.report_is_acceptable:
        print(f"RETRYING Report Generation (Attempt {state.report_retry_count + 1})")
        prompt += f"""
        The previous attempt FAILED.
        The evaluator rejected the previous report for the following reason: {state.report_feedback}
        You must address this feedback and generate an improved, more accurate, detailed report.
        """
        state.report_retry_count += 1

    result = structured_llm.invoke(prompt)
    state.report = result.report
    print("Report has been generated")
    return state