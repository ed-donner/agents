from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field
from state import ResearchState
from langgraph.types import interrupt
from dotenv import load_dotenv

load_dotenv(override=True)

llm = ChatOpenAI(model="gpt-4o-mini")

class ClarifyingQuestions(BaseModel):
    questions: list[str] = Field(description="Three insightful clarifying questions.")

def clarifier_node(state: ResearchState) -> ResearchState:
    instructions = """
    You are a research analyst. Your first job is to understand the user's query.
    Given a research query, your goal is to generate 3 brief, insightful clarifying questions to help focus the research and 
    understand the user's true intent.
    Do not answer the query. Only generate questions.
    """
    print("EXECUTING: CLARIFIER NODE")
    structured_llm = llm.with_structured_output(ClarifyingQuestions)
    result = structured_llm.invoke(f"User query: {state.user_query}\n{instructions}")
    questions = result.questions


    answers = interrupt({
        "clarifying_questions": questions,
        "instruction": "Please answer these before continuing."
    })

    state.clarifying_questions = questions
    state.clarifying_answers = answers
    return state
