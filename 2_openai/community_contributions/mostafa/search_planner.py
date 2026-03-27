from pydantic import BaseModel, Field
from agents import Agent, Runner


NUMBER_OF_SEARCHES = 3

INSTRUCTIONS = f'''You are a search planner. Your task is to create a plan for searching for information on the internet. 
        You will be given a query, and you need to come up with a plan for how to search for that information.
        Your plan should include the following steps:
        1. Identify the key terms in the query.
        2. Create the top {NUMBER_OF_SEARCHES} search queries that will help find the information you need.
        3. For each search query, identify the reasoning behind prioritizing it and what kind of information you expect to find from it.
        4. Return the search plan in a structured format.'''


class WebSearchItem(BaseModel):
    reasoning: str = Field(
        description="The reasoning behind prioritizing this search query and what kind of information is expected to be found from it.")
    query: str = Field(
        description="The search query to be used for searching for information on the internet.")


class WebSearchPlan(BaseModel):
    query: str = Field(description="The original query for which the search plan was created.")
    searches: list[WebSearchItem] = Field(description=f"A list of {NUMBER_OF_SEARCHES} search queries to perform to best answer the query and their reasoning.")


class PlannerAgent:
    def __init__(self):
        self.agent = Agent(
            name="Search Planner",
            instructions=INSTRUCTIONS,
            model="gpt-4o-mini",
            output_type=WebSearchPlan,
        )

    async def run(self, query: str) -> WebSearchPlan:
        ''' Plan the search strategy based on the clarified query '''
        print('Planning search strategy ...')
        result= await Runner.run( self.agent,
            f'Query: {query}\n\n'
        )
        search_plan = result.final_output_as(WebSearchPlan)
        print(f'Will perform {len(search_plan.searches)} searches:')
        return search_plan

