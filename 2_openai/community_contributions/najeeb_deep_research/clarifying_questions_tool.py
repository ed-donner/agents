from agents import function_tool, RunContextWrapper
from pydantic import BaseModel
from state import session_state

class ClarifyingAnswers(BaseModel):
    question_1: str
    question_2: str
    question_3: str
    original_query: str


@function_tool
async def clarifying_questions(
    ctx: RunContextWrapper,
    query: str,
) -> ClarifyingAnswers:
    """
    Asks the user 3 clarifying questions about their original query.
    Call this tool ONCE at the start with the user's original query.
    Do NOT call it again on the answers.

    Args:
        query: The user's original query
    """
    answers = session_state.get("answers", ["", "", ""])

    return ClarifyingAnswers(
        original_query=query,
        question_1=answers[0],
        question_2=answers[1],
        question_3=answers[2],
    )