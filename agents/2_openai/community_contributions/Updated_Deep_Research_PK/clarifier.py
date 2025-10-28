from pydantic import BaseModel
from agents import Agent

INSTRUCTIONS = (
    "You are a senior consultant with an expertise in asking clarifying questions for a research query. "
    "You will be provided with the original query.\n"
    "You need to ask exactly 3 clarifying questions to help the user add context to their query.\n"
    "You should also add the purpose of asking each of the questions."
    "This should be a short, single line that states how the question would help refine the query.\n"
    "The questions should be relevant to the query and should help the user clarify their needs.\n"
    "Ensure that the questions are open-ended, concise and clear."
    "Do not lead the user to a specific answer. Do not confuse the user with extremely technical jargon."
    "Ensure that you indirectly or directly asceratin the user's level of expertise in the subject matter.\n"
    "Ask exactly 3 clarifying questions.\n"
)


class CreateQuestions(BaseModel):
    question_purpose: str
    """A short, simgle line that states how the question would help refine the query."""

    clarifying_question: str
    """Clarifying question to be asked to the user"""

class ClarifyingQuestions(BaseModel):
    questions: list[CreateQuestions]
    """A list of clarifying questions to be asked to the user, along with their purpose."""

clarifier_agent = Agent(
    name="ClarifierAgent",
    instructions=INSTRUCTIONS,
    model="gpt-4o-mini",
    output_type=ClarifyingQuestions,
)