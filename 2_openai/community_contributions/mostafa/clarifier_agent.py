from pydantic import BaseModel, Field
from agents import Agent, Runner


INSTRUCTION = '''
You are a research expert. 
Your task is to decide whether the user's query is clear enough for a web search. 
If the question is clear, you should respond with setting the is_clear to true, Don't ask any clarifying questions, and the refined_query should be the same as the original query.
If the question is not clear, you should ask a clarifying question to get more information from 
the user. 
If the query is a follow-up with answers to previous clarifying questions, you should refine the 
original query with the new information and ask any additional clarifying questions if needed.
The refined query will be used for the web search, so it should be as clear and specific as possible.
Provide your answer with the provided output format.
'''


class ClarificationQuestion(BaseModel):
    question: str = Field(
        description='The clarifying question to ask the user.')
    reason: str = Field(description='The reason why this is important to ask.')


class ClarificationAnswer(BaseModel):
    is_clear: bool = Field(
        description='Whether the question is clear enough to be answered.')
    questions: list[ClarificationQuestion] = Field(
        description='List of clarifying questions if the question is not clear. If the question is clear, this should be an empty list.')
    refined_query: str = Field(
        description='A refined version of the original query that incorporates the clarifying questions. If the question is clear, this should be the same as the original query.')


class ClarifierAgent:
    def __init__(self):
        self.agent= Agent(
            name='Clarifier Agent',
            instructions=INSTRUCTION,
            model='gpt-4o-mini',
            output_type=ClarificationAnswer,
        )

    async def run(self, query) -> ClarificationAnswer:
        ''' Determine whether the user's query is clear enough for a web search, and if not, ask a clarifying question. '''
        print('Thinking about the clarity of the question...')
        clarification_answer = await Runner.run(self.agent, query)
        return clarification_answer.final_output_as(ClarificationAnswer)
