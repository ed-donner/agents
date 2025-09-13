from agents import Agent, WebSearchTool, ModelSettings, OpenAIChatCompletionsModel
from pydantic import BaseModel, Field, AnyUrl
from openai import AsyncOpenAI

import os
from dotenv import load_dotenv

load_dotenv(override=True)

openai_api_key = os.getenv('OPENAI_API_KEY')


INSTRUCTIONS = """You are a research assistant. 
Given a concrete search term and 3 clarifying questions and answers.
Search exactly for the given term, prioritizing recent or constrained results when a timeframe is provided. 
You must use the WebSearchTool and not rely on prior knowledge.
The summary must 3-5 paragraphs and less than 500 words.
Capture the main points. Write in complete sentences and use the right grammar and expressions. 
Use 3-5 different sources.
Every claim you state must be supportable by a listed source.
List all sources as a list at the end with a short title and URL
If the evidence is weak, briefly say so and note what information would still be needed.
Do not inlcude any other commentary."""


class SourceItem(BaseModel):
    title: str = Field(description = 'Short title of the source')
    url: str = Field(description = '"HTTP/HTTPS URL (must start with http(s)://)"')

class SearchOutput(BaseModel):
    summary: str = Field(description = 'Return a summary no longer than 500 words and 3-5 paragraphs.')
    sources: list[SourceItem] = Field(description = 'Provide a list with the sources including title and URL for each',
                                      min_items = 3,
                                      max_items = 5)



search_agent = Agent(
    name = 'SearchAgent',
    instructions = INSTRUCTIONS,
    tools = [WebSearchTool(search_context_size = 'low')],
    model = 'gpt-4o-mini',
    model_settings = ModelSettings(tool_choice = 'required'),
    output_type = SearchOutput
)

search_tool = search_agent.as_tool(tool_name = 'search_web', tool_description = 'Search web for given term and provide sources')