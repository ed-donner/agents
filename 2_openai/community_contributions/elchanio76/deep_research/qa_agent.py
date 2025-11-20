from agents import Agent, WebSearchTool
from pydantic import BaseModel, Field
from typing import List

INSTRUCTIONS = ("You are a data analyst assistant, answering questions about a report."
                "Your job is to analyze the report's context and provide the most accurate answer possible."
                "If you cannot answer the questions based on the provided context, you can search the web for additional sources."
            )

class QA_Response(BaseModel): 
    question: str = Field(description="The question that was asked")
    answer: str = Field(description="The answer to the question")
    sources: List[str] = Field(description="List of unique source URLs used to answer the question", max_length=10)

qa_agent = Agent(
    name="QA agent",
    instructions=INSTRUCTIONS,
    tools=[WebSearchTool(search_context_size="high")],
    output_type=QA_Response,
    model="gpt-4o-mini",
)