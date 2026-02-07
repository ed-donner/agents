import asyncio
from typing import AsyncGenerator

from agents import (
    Agent,
    Runner,
    gen_trace_id,
    trace,
)

from .hook import ResearchRunHook
from .tool import (
    search_planning_tool,
    search_tool,
    send_email_tool,
    write_report_tool,
)


# Sentinel to signal end of stream
END_OF_STREAM = object()


INSTRUCTIONS = """
You are Deep Research Agent, an AI specialized in conducting in-depth research on various topics.
Your goal is to gather information, analyze data, and compile comprehensive reports based on user queries.
Follow these steps to complete your tasks:
1. Plan the Research Strategy: Use the Search Planning Tool to outline a research strategy, identifying key areas
to explore.
2. Conduct Research: Utilize the Search Tool to gather relevant information.
3. Analyze Findings: Review and analyze the collected data to extract meaningful insights.
   Continue using the Search Tool as needed to fill in any gaps.
4. Write the Report: Employ the Write Report Tool to write a report that addresses the user's query.
5. Deliver the Report: Use the Send Email Tool to send the completed report to the user or specified recipients.
Use all the tools provided to you effectively. Do not attempt to perform tasks outside of your capabilities.
"""

research_agent = Agent(
    name="Deep Research Agent",
    instructions=INSTRUCTIONS,
    model="gpt-5.2",
    tools=[search_planning_tool, search_tool, write_report_tool, send_email_tool],
)


async def run_agent(input: str, queue: asyncio.Queue) -> None:
    """Execute the agent with user input and queue progress messages and final output.

    Args:
        input: The user's message to process.
        queue: Queue to send progress messages and final output.
    """
    hook = ResearchRunHook(queue)
    result = await Runner.run(
        starting_agent=research_agent,
        input=input,
        hooks=hook,
    )
    await queue.put(result.final_output)
    await queue.put(END_OF_STREAM)


async def generate_responses(input: str) -> AsyncGenerator[str, None]:
    """Execute the agent with user input and yield progress messages and final output.

    Args:
        input: The user's message to process.

    Yields:
        Progress messages from hooks and the final report.
    """
    trace_id = gen_trace_id()
    print("Starting research agent...")
    print(f"View trace: https://platform.openai.com/traces/trace?trace_id={trace_id}")

    queue: asyncio.Queue[str | object] = asyncio.Queue()

    with trace("Deep Research", trace_id=trace_id):
        # Start run_agent as a background task
        task = asyncio.create_task(run_agent(input, queue))

        # Yield messages as they arrive
        while True:
            message = await queue.get()
            if message is END_OF_STREAM:
                break
            yield message  # type: ignore[misc]

        # Ensure task completes (propagate any exceptions)
        await task
