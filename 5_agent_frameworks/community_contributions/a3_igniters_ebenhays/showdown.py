from typing import AsyncGenerator, cast

from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.base import TaskResult
from autogen_agentchat.conditions import MaxMessageTermination, TextMentionTermination
from autogen_agentchat.messages import (
    BaseAgentEvent,
    BaseChatMessage,
    BaseTextChatMessage,
    HandoffMessage,
    ModelClientStreamingChunkEvent,
    MultiModalMessage,
    StopMessage,
    UserInputRequestedEvent,
)
from autogen_agentchat.teams import SelectorGroupChat
from autogen_ext.models.openai import OpenAIChatCompletionClient
from autogen_ext.tools.langchain import LangChainToolAdapter
from dotenv import load_dotenv
from langchain_community.tools import DuckDuckGoSearchRun

DEBATE_END_MARKER = "DEBATE_CLOSED"

SPEAKERS: dict[str, str] = {
    "BlueEbenezer": "Chelsea",
    "CitizenShark": "Manchester City",
    "ThePundit": "Moderator",
}


def build_football_debate_team() -> SelectorGroupChat:
    """Construct the Chelsea vs City debate team"""
    load_dotenv(override=True)
    model_client = OpenAIChatCompletionClient(model="gpt-4o")

    search_tool = LangChainToolAdapter(DuckDuckGoSearchRun())

    chelsea_agent = AssistantAgent(
        name="BlueEbenezer",
        model_client=model_client,
        tools=[search_tool],
        system_message=(
            "You are a die-hard Chelsea fan. You value 'Proper Chels' grit, "
            "the legacy of 2012 and 2021, and you never miss a chance to mention "
            "that London is Blue. You are skeptical of 'oil money' clubs. "
            "Use the search tool to find the latest Chelsea stats to win your arguments."
            "Your answers should be at least 10 words and concise and to the point. "
            f"End conversation when you see `{DEBATE_END_MARKER}`; only the moderator may use that to close the debate."
        ),
    )

    city_agent = AssistantAgent(
        name="CitizenShark",
        model_client=model_client,
        tools=[search_tool],
        system_message=(
            "You are a tactical Manchester City fan. You believe in 'Pep-ball', "
            "possession stats, and the Treble. You think Chelsea is a chaotic circus. "
            "You use data and 'beautiful football' logic to shut down emotional arguments. "
            "Use the search tool to find recent City match stats."
            "Your answers should be at least 10 words and concise and to the point. "
            f"End conversation when you see `{DEBATE_END_MARKER}`; only the moderator may use that to close the debate."
        ),
    )

    mediator = AssistantAgent(
        name="ThePundit",
        model_client=model_client,
        system_message=(
            "You are a professional sports moderator. Your job is to facilitate "
            "a heated but respectful debate. Ensure both sides get to speak. "
            "After 2-3 rounds of banter, deliver one final message that: (1) summarizes both sides, "
            "(2) gives a fair verdict, and (3) closes the segment. "
            "In that final message only, end with your summary and verdict, then on its own last line "
            f"output exactly this token and nothing else on that line: {DEBATE_END_MARKER} "
            "Do not use that token in any earlier message. "
            "Keep the verdict portion at least 50 words, concise and to the point."
        ),
    )

    termination = TextMentionTermination(
        DEBATE_END_MARKER, sources=["ThePundit"]
    ) | MaxMessageTermination(max_messages=30)

    return SelectorGroupChat(
        participants=[chelsea_agent, city_agent, mediator],
        model_client=model_client,
        termination_condition=termination,
        allow_repeated_speaker=False,
    )


async def stream_debate_transcript(
    team: SelectorGroupChat, task: str
) -> AsyncGenerator[str, None]:
    """
    Stream the debate as plain text. Each yielded value is the full transcript so far.
    """
    parts: list[str] = []
    streaming_chunks: list[str] = []

    def emit() -> str:
        return "".join(parts)

    async for message in team.run_stream(task=task):
        if isinstance(message, TaskResult):
            parts.append(
                f"\n{'─' * 10} Summary {'─' * 10}\n"
                f"Messages: {len(message.messages)} | Stop: {message.stop_reason}\n"
            )
            yield emit()
            return

        if isinstance(message, UserInputRequestedEvent):
            continue

        message = cast(BaseAgentEvent | BaseChatMessage, message)

        if isinstance(message, ModelClientStreamingChunkEvent):
            parts.append(message.to_text())
            streaming_chunks.append(message.content)
            yield emit()
        else:
            if streaming_chunks:
                streaming_chunks.clear()
                parts.append("\n")
            if isinstance(message, MultiModalMessage):
                parts.append(message.to_text(iterm=False) + "\n")
            else:
                parts.append(message.to_text() + "\n")
            yield emit()


def speaker_heading(source: str) -> str:
    return SPEAKERS.get(source, source.replace("_", " "))


def turn_markdown(source: str, message: BaseTextChatMessage | MultiModalMessage) -> str:
    if isinstance(message, MultiModalMessage):
        body = message.to_text(iterm=False).strip()
    else:
        body = message.to_text().strip()
    if DEBATE_END_MARKER in body:
        body = body.replace(DEBATE_END_MARKER, "").strip()
    label = speaker_heading(source)
    return f"\n\n#### {label}\n\n{body}\n"


async def stream_live_transcript(
    team: SelectorGroupChat, task: str
) -> AsyncGenerator[str, None]:
    """
    Stream a live transcript suitable for end users for finished speaker.
    """
    parts: list[str] = []

    def emit() -> str:
        return "".join(parts)

    async for message in team.run_stream(task=task):
        if isinstance(message, TaskResult):
            parts.append(
                "*This exchange has finished.* "
                f"{len(message.messages)} messages · {message.stop_reason}\n"
            )
            yield emit()
            return

        if isinstance(message, UserInputRequestedEvent):
            continue

        if isinstance(message, BaseTextChatMessage):
            if isinstance(message, (StopMessage, HandoffMessage)):
                continue
            if message.source == "user":
                continue
            parts.append(turn_markdown(message.source, message))
            yield emit()
            continue

        if isinstance(message, MultiModalMessage):
            if message.source == "user":
                continue
            parts.append(turn_markdown(message.source, message))
            yield emit()
            continue

    yield emit()
