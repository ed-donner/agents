from agents import Agent, WebSearchTool, ModelSettings, Runner
from search_planner import WebSearchItem


INSTRUCTIONS = '''
You are a research assistant. 
You will be given a search term, you will search for it on the internet and produce a consise summary of the results. 
The summary must be 2-3 paragraphs and less than 300 words.
Capture the main points and key insights from the search results. 
Do not include any personal opinions or irrelevant information. 
Focus on providing a clear and informative summary based on the search results. 
This will be consumed by another agent to synthesize a final report, so it's vital you capture the essnce and ignore any fluff. 
Don't include any additional commentary other than the summary itself.'''


class SearchAgent:
    def __init__(self):
        self.search_agent = Agent(
            name='Search Agent',
            instructions=INSTRUCTIONS,
            tools=[WebSearchTool(search_context_size='low')],
            model='gpt-4o-mini',
            model_settings=ModelSettings(tool_choice='required'),
        )

    async def run(self, item: WebSearchItem) -> str:
        ''' Search for the query and produce a concise summary of the results '''
        input = f'Search term: {item.query}\nReason for searching: {item.reasoning}\n\n'
        search_summary = await Runner.run(
            self.search_agent, input
        )
        return search_summary.final_output_as(str)
