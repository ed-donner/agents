from pydantic import BaseModel, Field 
from typing import Optional
from agents import Agent, OpenAIChatCompletionsModel
from openai import AsyncOpenAI

import os
from dotenv import load_dotenv

load_dotenv(override=True)

openai_api_key = os.getenv('OPENAI_API_KEY')


INSTRUCTIONS = """You are an Evaluator assistant.
You will be provided with the user query and the report with the final research results.
Check the structure, length, headings and markdowns.
Check if all sources are listed including a title and the URL.
Check the grammar and spelling.
Score the report (integer 0-5) and give feedback for the given score including the relevance, completeness, evidence, clarity.
If you found any issues list them.
If necessary rewrite the paragraph.
Do not introduce new facts, only restructure, clarify, deduplicate and imporve flow and headings if necessary.
Return only JSON that matches the schema. No extra commentary or markdown outside the fields"""


class FeedbackInput(BaseModel):
    relevance: str
    completeness: str
    evidence: str
    clarity: str

class Evaluation(BaseModel):
    ok: bool = Field(description = 'True if score >=3, else False')
    score: int
    issues: list[str] = Field(description = 'List any issues found in the report')
    feedback_report: list[FeedbackInput] = Field(description = 'Feedback texts per dimension')
    revised_markdown: Optional[str] = Field(default = None,
                                            description = 'Rewritten report when necessary; null if no rewrite')
    change_log: Optional[list[str]] = Field(default = None,
                                            description = 'Summarizing edits; null if ni rewrite')

eval_agent = Agent(
    name = 'EvalAgent',
    instructions = INSTRUCTIONS,
    model = 'gpt-4o-mini',
    output_type = Evaluation
)

eval_tool = eval_agent.as_tool(tool_name = 'evaluation', tool_description = 'Eavaluates final report (0-5); lists issues and feedback')