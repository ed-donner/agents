from agents import Agent, Runner, function_tool, ModelSettings
from planner_agent import planner_agent
from search_agent import search_agent
from analyser_agent import analyser_agent
from writer_agent import writer_agent
import asyncio

RESEARCH_MANAGER_INSTRUCTIONS = """
You manage a deep research workflow.

Assume the user has already been asked and answered three clarification questions
via the UI layer. You will receive both the topic and the user's answers.

Your workflow:

1) Use the topic + user answers as research context
2) Plan searches using the Planner Agent
3) Execute searches using the Search Agent
4) Analyse findings using the Analyser Agent
   - Loop until research is complete or max iterations reached
5) When ready, hand off to the Writer Agent to produce a full research report
"""


@function_tool
async def research_workflow(topic: str, user_answers: str):
    """
    Coordinate the research workflow until it is complete.
    This tool is invoked directly by the Research Manager agent.
    """
    # Initial context includes topic + user clarification answers
    research_context = (
        f"Research Topic:\n{topic}\n\n"
        f"User Clarification Answers:\n{user_answers}\n\n"
    )

    combined_results = []
    iteration = 0
    max_iterations = 2

    # Loop: plan → search → analyse
    while iteration < max_iterations:
        # 1. Plan searches
        yield f"Planning web search... iteration {iteration}"
        planner_result = await Runner.run(planner_agent, research_context)
        searches = planner_result.final_output
        
        # 2. Execute searches concurrently
        yield f"Starting web search... iteration {iteration}"
        tasks = [Runner.run(search_agent, q.query) for q in searches.searches]
        search_results = await asyncio.gather(*tasks)

        # 3. Collect summaries
        yield f"Collating web search results... iteration {iteration}"
        combined_results.extend([r.final_output for r in search_results])

        # 4. Analyse completeness
        yield f"Analysing quality of search results... iteration {iteration}"
        analysis = await Runner.run(analyser_agent, str(combined_results))
        if analysis.final_output.research_complete:
            break

        # If incomplete, append reason to context and iterate again
        research_context += f"\nAdditional research needed: {analysis.final_output.reason}\n"
        iteration += 1

    # Prepare clean text for writer
    summaries_text = "\n\n---\n\n".join(combined_results)

    writer_input = (
        "You are writing a full research report.\n\n"
        f"Original Topic:\n{topic}\n\n"
        f"User Clarification Answers:\n{user_answers}\n\n"
        f"Initial Research Summaries:\n{summaries_text}\n"
    )

    yield "Searchs complete, writing report..."
    writer_result = await Runner.run(writer_agent, writer_input)
    return writer_result.final_output


# Research Manager agent definition
research_manager_agent = Agent(
    name="Research Manager",
    instructions=RESEARCH_MANAGER_INSTRUCTIONS,
    tools=[research_workflow],
    handoffs=[writer_agent],
    model="gpt-4o-mini",
    model_settings=ModelSettings(tool_choice="required"),
)