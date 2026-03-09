from agents import Agent, Runner, function_tool, ModelSettings
from planner_agent import planner_agent
from search_agent import search_agent
from analyser_agent import analyser_agent
from writer_agent import writer_agent
import asyncio

RESEARCH_MANAGER_INSTRUCTIONS = """
You manage a deep research workflow.

Steps:
1) Ask 3 clarification questions
2) Plan searches
3) Execute searches
4) Analyse findings
5) When ready handoff to writer agent
"""

@function_tool
async def research_workflow(topic: str, user_answers: str):
    """Coordinate the research workflow until it is complete"""
    research_context = f"{topic}\nUser answers:\n{user_answers}\n"
    combined_results = []

    iteration = 0
    max_iterations = 3

    # search_agent - analyser_agent loop until the research is deemed complete, max 3 iterations
    while iteration < max_iterations:
        planner_result = await Runner.run(planner_agent, research_context)
        searches = planner_result.final_output
        tasks = [Runner.run(search_agent, q.query) for q in searches.searches]
        search_results = await asyncio.gather(*tasks)
        combined_results.extend([r.final_output for r in search_results])
        analysis = await Runner.run(analyser_agent, str(combined_results))
        analysis_outcome = analysis.final_output.research_complete
        if analysis_outcome:
            break
        research_context += analysis.final_output.reason
        iteration += 1
    
    writer_input = f"Write a full research report based on:{combined_results}"
    writer_result = await Runner.run(writer_agent, writer_input)
    return writer_result.final_output


@function_tool
def ask_user_clarifications(questions: str) -> str:
    """
    Present the clarification questions to the user and return their answers.
    The UI layer (Gradio) will display the questions and collect the user's response.
    """
    return questions


# Research Manager as an agent with handoffs to writer_agent
research_manager_agent = Agent(
    name="Research Manager",
    instructions=RESEARCH_MANAGER_INSTRUCTIONS,
    tools=[research_workflow, ask_user_clarifications],
    handoffs=[writer_agent],
    model="gpt-4o-mini",
    model_settings=ModelSettings(tool_choice="required"),
)