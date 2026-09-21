"""Week 5 capstone (AutoGen) - autogen-core: agents that message each other on a runtime.

Week 5 has two layers. reflection_team.py shows the high-level AgentChat (a RoundRobinGroupChat).
This is the lower layer - autogen-core: a runtime delivers typed messages between RoutedAgents, each
handling them with @message_handler. A coordinator asks several domain agents (each backed by an LLM)
for a startup idea in their field and collects the replies - the message-passing backbone the
distributed "agent world" capstone is built on.

Run: uv run python agent_world.py     (needs OPENAI_API_KEY)
"""
import asyncio
from dataclasses import dataclass

from autogen_core import (AgentId, MessageContext, RoutedAgent, SingleThreadedAgentRuntime,
                          message_handler)
from autogen_core.models import SystemMessage, UserMessage
from autogen_ext.models.openai import OpenAIChatCompletionClient
from dotenv import load_dotenv

load_dotenv(override=True)


@dataclass
class Ask:
    topic: str


@dataclass
class Idea:
    field: str
    idea: str


class DomainAgent(RoutedAgent):
    def __init__(self, field: str):
        super().__init__(f"{field} expert")
        self.field = field
        self.model = OpenAIChatCompletionClient(model="gpt-4o-mini")

    @message_handler
    async def handle(self, message: Ask, ctx: MessageContext) -> Idea:
        result = await self.model.create([
            SystemMessage(content=f"You are an entrepreneur in {self.field}. Answer in one sentence."),
            UserMessage(content=f"Propose a startup idea that uses: {message.topic}", source="coordinator"),
        ])
        return Idea(field=self.field, idea=result.content.strip())


async def main():
    runtime = SingleThreadedAgentRuntime()
    fields = ["healthcare", "education", "logistics"]
    for f in fields:                                          # register one agent type per field
        await DomainAgent.register(runtime, f, lambda f=f: DomainAgent(f))
    runtime.start()
    ideas = [await runtime.send_message(Ask(topic="AI agents"), AgentId(f, "default")) for f in fields]
    await runtime.stop()
    for i in ideas:
        print(f"[{i.field}] {i.idea}")


if __name__ == "__main__":
    asyncio.run(main())
