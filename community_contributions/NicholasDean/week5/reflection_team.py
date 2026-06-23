"""Week 5 (AutoGen) deliverable — a minimal two-agent reflection team.

AutoGen AgentChat is conversational: agents take turns in a team and refine each other's work. Here
a Writer drafts and a Critic reviews; a RoundRobinGroupChat alternates them, and the loop ends when
the Critic replies APPROVE (TextMentionTermination). Everything is async.

Run: uv run python reflection_team.py "write a tagline for a digital-twin bot"   (needs OPENAI_API_KEY)
"""
import asyncio
import sys

from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.conditions import TextMentionTermination
from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_agentchat.ui import Console
from autogen_ext.models.openai import OpenAIChatCompletionClient
from dotenv import load_dotenv

load_dotenv(override=True)
model_client = OpenAIChatCompletionClient(model="gpt-4o-mini")

writer = AssistantAgent(
    name="writer",
    model_client=model_client,
    system_message="You write and revise the piece. Apply the critic's feedback on each turn.",
)
critic = AssistantAgent(
    name="critic",
    model_client=model_client,
    system_message="Critique the writer's latest draft with specific, actionable feedback. "
                   "When it is genuinely good, reply with just the word APPROVE.",
)

# RoundRobinGroupChat alternates the agents; the team stops when "APPROVE" is mentioned.
team = RoundRobinGroupChat(
    [writer, critic],
    termination_condition=TextMentionTermination("APPROVE"),
    max_turns=6,
)


async def main(task: str):
    await Console(team.run_stream(task=task))      # stream the back-and-forth to the terminal
    await model_client.close()


if __name__ == "__main__":
    task = " ".join(sys.argv[1:]) or "Write a short, vivid product tagline for a digital-twin chatbot."
    asyncio.run(main(task))
