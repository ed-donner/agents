from openai import AsyncOpenAI
from agents import Runner, Agent, trace, gen_trace_id,function_tool, OpenAIChatCompletionsModel
from writer_agent import writer_agent, ReportData
from planner_agent import planner_agent,WebSearchPlan, WebSearchItem
from search_agent import search_agent
from search_utils import plan_searches, perform_searches, search
import os, asyncio
anthropic_api_key = os.getenv('ANTHROPIC_API_KEY')
claude_base_url = "https://api.anthropic.com/v1/"
anthropic_client = AsyncOpenAI(base_url=claude_base_url, api_key=anthropic_api_key)

claude_model = OpenAIChatCompletionsModel(model="claude-opus-4-6", openai_client=anthropic_client)

orchestrator_instructions = f"You are an orchestrator agent. You run after each failed evaluation and, based on the query, the current \
    report and the evaluation feedback, you should decide whether to only rewrite the report \
    or peform more searches and rewrite the report. If you performed more searches, you should also rewrite the report.\
    When you are happy with the report, you should accept it. "




@function_tool
async def search_more( query: str, previous_searchplan:WebSearchPlan, previous_results: list[str]) -> WebSearchPlan:
    """ Plan another search plan and perform the searches in that new plan """
    new_searchplan = await plan_searches( query, previous_searchplan)
    new_search_results = await perform_searches(new_searchplan, previous_results)
    return new_search_results

@function_tool 
async def rewrite_report(query: str, search_results: list[str], report:str, feedback:str)->ReportData :
    """ Rewrite the report, taking into account the feedback """
    print("Rewriting report...")
    input = f"Original query: {query}\nSearch results: {search_results}\n\nPrevious report:\n{report}\nEvaluation feedback:\n{feedback}\n\nPlease rewrite the report taking the feedback into account."

    result = await Runner.run(
        writer_agent,
            input,
        )

    print("Finished rewriting report")
    return result.final_output_as(ReportData)    

@function_tool
def accept_report(report: ReportData) -> ReportData:
    """Accept the current report as adequate and return it for sending."""
    return report
        
orchestrator_agent = Agent(
    name="Orchestrator Agent", 
    instructions=orchestrator_instructions, 
    tools = [rewrite_report, search_more, accept_report],
    model=claude_model,
    output_type = ReportData)

