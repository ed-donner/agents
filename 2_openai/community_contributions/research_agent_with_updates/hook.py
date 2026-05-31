import asyncio

from agents import (
    Agent,
    RunContextWrapper,
    RunHooks,
    Tool,
)


class ResearchRunHook(RunHooks):
    """Global run hooks that observe ALL agents in a run and queue progress messages.

    Attach to Runner.run() to receive events from every agent:

        queue = asyncio.Queue()
        await Runner.run(agent, input, hooks=ResearchRunHook(queue))
    """

    def __init__(self, queue: asyncio.Queue[str]) -> None:
        self.queue = queue

    async def on_tool_start(self, context: RunContextWrapper, agent: Agent, tool: Tool) -> None:
        """Called when any tool starts execution.

        Args:
            context: The run context
            agent: The agent that called the tool
            tool: The tool being executed
        """
        await self.queue.put(f"Starting: {tool.name}...")

    async def on_tool_end(self, context: RunContextWrapper, agent: Agent, tool: Tool, result: str) -> None:
        """Called after any tool completes.

        Args:
            context: The run context
            agent: The agent that called the tool
            tool: The tool that completed
            result: The string result from the tool
        """
        await self.queue.put(f"Completed: {tool.name}")
