import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

load_dotenv(override=True)
openrouter_api_key = os.getenv("OPENROUTER_API_KEY")
openrouter_url = "https://openrouter.ai/api/v1"

class ClarifyingQuestions(BaseModel):
    question_1: str = Field(description="First clarifying question")
    question_2: str = Field(description="Second clarifying question")
    question_3: str = Field(description="Third clarifying question")


async def generate_clarifying_questions(task_description: str) -> tuple[str, str, str]:
    llm = ChatOpenAI(base_url=openrouter_url, api_key=openrouter_api_key, model="gpt-4o-mini", temperature=0.3)
    structured = llm.with_structured_output(ClarifyingQuestions)
    prompt = (
        "Given the user's task below, write exactly three short, specific, practical "
        "clarifying questions that would help complete the task well. "
        "Each question must be different and clear.\n\nTask:\n"
        f"{task_description}"
    )
    out = await structured.ainvoke(prompt)
    return out.question_1, out.question_2, out.question_3
