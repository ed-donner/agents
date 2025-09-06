from pydantic import BaseModel, Field
from agents import Agent

import os
from dotenv import load_dotenv

load_dotenv(override=True)

openai_api_key = os.getenv('OPENAI_API_KEY')

INSTRUCTIONS = """ You are a helpful assistant. 
    Given a user's research query you come up with 3 clarifying questions.

    Rules:
        - Keep the questions short (one sentence each question). 
        - Do not answer the questions yourself 
        - Ask exactly 3 questions
        - Return JSON only
        - Every question must end with a '?' """


class Clarification(BaseModel):
    questions: list[str] = Field(description = "A list of exactly 3 questions",
                                 min_items = 3,
                                 max_items = 3)


clarifier_agent = Agent(
    name = 'ClarifyAgent',
    instructions = INSTRUCTIONS,
    model = 'gpt-4o-mini',
    output_type = Clarification

)

clarify_tool = clarifier_agent.as_tool(tool_name = 'clarify', tool_description = 'Ask 3 clarifying questions')
