from pydantic import BaseModel, Field
from agents import Agent, OpenAIChatCompletionsModel
from openai import AsyncOpenAI

import os
from dotenv import load_dotenv

load_dotenv(override=True)

google_api_key = os.getenv('GOOGLE_API_KEY')
GEMINI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai/"
gemini_client = AsyncOpenAI(base_url=GEMINI_BASE_URL, api_key=google_api_key)
gemini_model = OpenAIChatCompletionsModel(model="gemini-2.0-flash", openai_client=gemini_client)




INSTRUCTIONS = """ You are a helpful assistant answering questions.
    You receive a user query and 3 clarifying questions. 

    Return a JSON that matches the schema:
        'qa': exactly three items; each item must copy the question text and provide one answer (<= 3 sentences)
        'required fields': 'focus', 'sources', 'timeframe', 'depth' 
    Be precise and brief.

    Guidance: 
        - focus: short description of domain, e.g., like technical, ethical, academic etc 
        - sources: pick 1-3 preferred sources e.g., papers, docs, github, blogs 
        - timeframe: e.g., like last month, last 12 months, last 5 years 
        - depth: deep-dive or quick overview 
        
    These fields are always required. 
    Do not add extra fields."""


class AnswerQuestions(BaseModel):
    question: str = Field(description = 'One of the given question')
    answer: str = Field(description = 'One answer for each of the questions')


class ClarificationAnswers(BaseModel):
    qa: list[AnswerQuestions] = Field(description = 'Question - Answer pair for all clarifying questions',
                           min_items = 3,
                           max_items = 3)
    focus: str = Field(description = 'Give back a specific focus')
    sources: list[str] = Field(description = '1-3 preferred source types.')
    timeframe: str = Field(description = 'Time constraint')
    depth: str = Field(description = 'Decide between deep-dive or quick overview')


answer_agent = Agent(
    name = 'AnswerAgent',
    instructions = INSTRUCTIONS,
    model = gemini_model,
    output_type = ClarificationAnswers

)

answer_tool = answer_agent.as_tool(tool_name = 'answer_clarifications', tool_description = 'Answer 3 clarifying questions')
