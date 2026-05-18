import asyncio
import json

from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.conditions import TextMentionTermination
from autogen_agentchat.messages import TextMessage
from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_ext.models.openai import OpenAIChatCompletionClient
from dotenv import load_dotenv
from pydantic import ValidationError

from config import MODEL, OPENAI_BASE_URL, build_model_info, needs_model_info
from schemas import EmailDraft
from tools import style_guide_tool, word_count_tool


load_dotenv(override=True)


def build_agents():
    client_kwargs = {}
    if OPENAI_BASE_URL:
        client_kwargs["base_url"] = OPENAI_BASE_URL
    if needs_model_info(MODEL):
        client_kwargs["model_info"] = build_model_info()

    research_client = OpenAIChatCompletionClient(model=MODEL, temperature=0.2, **client_kwargs)
    writer_client = OpenAIChatCompletionClient(
        model=MODEL,
        temperature=0.4,
        response_format=EmailDraft,
        **client_kwargs,
    )
    review_client = OpenAIChatCompletionClient(model=MODEL, temperature=0.1, **client_kwargs)

    researcher = AssistantAgent(
        name="researcher",
        model_client=research_client,
        tools=[style_guide_tool],
        reflect_on_tool_use=True,
        system_message=(
            "You are a research assistant. Use the style guide tool and summarize "
            "the key constraints and a single best benefit to emphasize."
        ),
    )

    writer = AssistantAgent(
        name="writer",
        model_client=writer_client,
        tools=[word_count_tool],
        reflect_on_tool_use=True,
        system_message=(
            "You are a copywriter. Produce a JSON response that follows the schema exactly. "
            "Apply the constraints from the researcher and keep the email concise."
        ),
    )

    reviewer = AssistantAgent(
        name="reviewer",
        model_client=review_client,
        system_message=(
            "Review the draft for clarity and word count. "
            "Respond with APPROVE if it is concise, professional, and under 120 words. "
            "Otherwise provide specific feedback."
        ),
    )

    return researcher, writer, reviewer


def extract_latest_draft(messages):
    for message in reversed(messages):
        if message.source == "writer":
            raw = message.content
            try:
                if isinstance(raw, dict):
                    data = raw
                else:
                    data = json.loads(raw)
                validated = EmailDraft.model_validate(data)
                return validated
            except (json.JSONDecodeError, ValidationError):
                return None
    return None


async def run_team():
    researcher, writer, reviewer = build_agents()

    termination = TextMentionTermination("APPROVE")
    team = RoundRobinGroupChat(
        [researcher, writer, reviewer],
        termination_condition=termination,
        max_turns=8,
    )

    prompt = (
        "Draft a launch email for a new AI Agents course aimed at software engineers. "
        "Audience: mid-level engineers transitioning into AI. "
        "Goal: encourage them to sign up for the waitlist."
    )

    result = await team.run(task=prompt)

    print("\n=== Conversation ===\n")
    for message in result.messages:
        print(f"{message.source}:\n{message.content}\n")

    draft = extract_latest_draft(result.messages)
    if draft:
        print("\n=== Parsed Draft ===\n")
        print(draft.model_dump_json(indent=2))
    else:
        print("\nNo valid structured draft found.")


if __name__ == "__main__":
    asyncio.run(run_team())
