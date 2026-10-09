from typing import Any
from datetime import datetime
from agents import Agent, AgentHooks, RunContextWrapper, Tool


class AgentLoggingHooks(AgentHooks):
    def __init__(self, display_name: str):
        self.event_counter = 0
        self.display_name = display_name

    def _get_timestamp(self) -> str:
        """Get simplified timestamp for logging (to the nearest second)."""
        return datetime.now().strftime("%H:%M:%S")

    async def on_start(self, context: RunContextWrapper, agent: Agent) -> None:
        self.event_counter += 1
        timestamp = self._get_timestamp()
        print(f"[{timestamp}] ({self.display_name}) {self.event_counter}: Agent {agent.name} started")

    async def on_end(self, context: RunContextWrapper, agent: Agent, output: Any) -> None:
        self.event_counter += 1
        timestamp = self._get_timestamp()
        print(
            f"[{timestamp}] ({self.display_name}) {self.event_counter}: Agent {agent.name} ended with output {output}"
        )

    async def on_handoff(self, context: RunContextWrapper, agent: Agent, source: Agent) -> None:
        self.event_counter += 1
        timestamp = self._get_timestamp()
        print(
            f"[{timestamp}] ({self.display_name}) {self.event_counter}: Agent {source.name} handed off to {agent.name}"
        )

    async def on_tool_start(self, context: RunContextWrapper, agent: Agent, tool: Tool) -> None:
        self.event_counter += 1
        timestamp = self._get_timestamp()
        print(
            f"[{timestamp}] ({self.display_name}) {self.event_counter}: Agent {agent.name} started tool {tool.name}"
        )

    async def on_tool_end(
        self, context: RunContextWrapper, agent: Agent, tool: Tool, result: str
    ) -> None:
        self.event_counter += 1
        timestamp = self._get_timestamp()
        print(
            f"[{timestamp}] ({self.display_name}) {self.event_counter}: Agent {agent.name} ended tool {tool.name} with result {result}"
        )
