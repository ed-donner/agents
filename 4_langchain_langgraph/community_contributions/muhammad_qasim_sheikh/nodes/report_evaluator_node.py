from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field
from state import ResearchState

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.2)

class ReportEvaluation(BaseModel):
    feedback: str = Field(description="Critique of the report.")
    score: float = Field(description="Numeric relevance score between 1 and 10.")
    is_acceptable: bool = Field(description="True if report meets expectations.")

def report_evaluator_node(state: ResearchState) -> ResearchState:
    print("EXECUTING: REPORT EVALUATOR NODE")
    structured_llm = llm.with_structured_output(ReportEvaluation)

    prompt = f"""
    You are a senior research analyst. You are provided with the the following inputs:
    1. Full research context including the original query and clarifications: {state.full_context}
    2. Draft of a report: {state.report}
    Your job is to evaluate the following: and 
    - Relevance to clarified intent.
    - Depth and factual grounding (use supporting summaries).
    - Structure and clarity.
    - Meets the length requirement of at least 1000 words
    Be strict with your judgement.
    Respond with
    - feedback (a short paragraph)
    - score (1 - 10) based on how well-written the report is
    - is_acceptable = True if report meets the clarified intent, else False
    """
    result = structured_llm.invoke(prompt)
    print(result)
    state.report_feedback = result.feedback
    state.report_score = result.score
    state.report_is_acceptable = result.is_acceptable

    if state.best_report_score is None or result.score > state.best_report_score:
        state.best_report_score = result.score
        state.best_report = state.report
        state.best_report_feedback = result.feedback

    print(f"Report evaluation: score={result.score:.2f}, acceptable={result.is_acceptable}")
    print("Feedback:", result.feedback, "\n")
    return state
