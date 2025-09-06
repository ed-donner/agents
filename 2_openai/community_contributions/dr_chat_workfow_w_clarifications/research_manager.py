from agents import Runner, trace, gen_trace_id, Agent, SQLiteSession
from search_agent import search_tool
from planner_agent import planner_tool
from writer_agent import writer_tool
from pydantic import BaseModel, Field

HOW_MANY_CLARIFICATIONS = 2

INSTRUCTIONS = f"""
    You are a senior researcher tasked with writing a cohesive report for a research query using the research_agent tools.
    You will be provided with the original query plus any previous follow-up questions related to the query for the user to answer and
    the user's answers to those questions.

    Follow these steps carefully:

    1. If the query is unclear, ask the user for clarifications and respond with a ResearchResponse object with the type 'follow_up' 
    and the questions to ask the user.  If the user's clarifications are not clear you make ask for more clarifications up to {HOW_MANY_CLARIFICATIONS} 
    more times.
    2. Generate search terms: Use the planner_agent tool to generate a list of search terms for the query.
    3. Perform searches: Use the search_agent tool to perform the searches for the search terms.
    4. Write report: Use the writer_agent tool to write the report for the query.

    The final output should be in markdown format, and it should be lengthy and detailed. Aim "
    for 5-10 pages of content, at least 1000 words."

    You should first come up with an outline for the report that describes the structure and "
    flow of the report. Then, generate the report and return that as your final output."
    The final output should be in markdown format, and it should be lengthy and detailed. Aim "
    for 5-10 pages of content, at least 1000 words."""



class ResearchResponse(BaseModel):
    type: str = Field(description="The type of response, either 'follow_up' or 'answer'")
    questions: list[str] = Field(description="A list of questions to ask the user if the type is 'follow_up'")
    content: str = Field(description="The content of the response if the type is 'answer'")


class ResearchManager:

    def __init__(self):
        self.manager_agent = Agent(
            name="Research Manager",
            instructions=INSTRUCTIONS,
            tools=[planner_tool, search_tool, writer_tool],
            model="gpt-4o-mini",
            output_type=ResearchResponse
        )

        self.session = SQLiteSession("research_session.db")
        self.trace_id = None

    async def run(self, user_input: str, input_type: str):
        assert input_type in ["query", "clarification"]

        if self.trace_id is None:
            self.trace_id = gen_trace_id()
        
        with trace("Research trace", trace_id=self.trace_id):
            print(f"View trace: https://platform.openai.com/traces/trace?trace_id={self.trace_id}")
            
            result = await Runner.run(
                self.manager_agent,
                f"{input_type}: {user_input}",
                session=self.session
            )
            return result.final_output_as(ResearchResponse)


    

