from typing import Any
from datetime import datetime
from agents import Agent, AgentHooks, RunContextWrapper, Tool

class NikhilAgentLogger(AgentHooks):
    def __init__(self, label: str):
        self.log_counter = 0
        self.label = label

    def _now(self) -> str:
        return datetime.now().strftime("%H:%M:%S")

    async def on_start(self, context: RunContextWrapper, agent: Agent) -> None:
        self.log_counter += 1
        print(f"[{self._now()}] ({self.label}) {self.log_counter}: Agent {agent.name} started")

    async def on_end(self, context: RunContextWrapper, agent: Agent, output: Any) -> None:
        self.log_counter += 1
        print(f"[{self._now()}] ({self.label}) {self.log_counter}: Agent {agent.name} ended with output {output}")

    async def on_handoff(self, context: RunContextWrapper, agent: Agent, source: Agent) -> None:
        self.log_counter += 1
        print(f"[{self._now()}] ({self.label}) {self.log_counter}: Agent {source.name} handed off to {agent.name}")

    async def on_tool_start(self, context: RunContextWrapper, agent: Agent, tool: Tool) -> None:
        self.log_counter += 1
        print(f"[{self._now()}] ({self.label}) {self.log_counter}: Agent {agent.name} started tool {tool.name}")

    async def on_tool_end(self, context: RunContextWrapper, agent: Agent, tool: Tool, result: str) -> None:
        self.log_counter += 1
        print(f"[{self._now()}] ({self.label}) {self.log_counter}: Agent {agent.name} ended tool {tool.name} with result {result}")
