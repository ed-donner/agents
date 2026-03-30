from __future__ import annotations

from contextlib import AsyncExitStack
from typing import Any

from openai import AsyncOpenAI
from agents import Agent, ModelSettings, OpenAIChatCompletionsModel, Runner, trace
from agents.mcp import MCPServerStdio

DEFAULT_MAX_TURNS = 28

DEMO_ACCOUNT = "blair"
DEMO_STYLE = (
    "Sound like a colleague advising a client: short, clear, and honest about risk. "
    "Keep stakes small and well explained."
)


def make_openrouter_model(client: AsyncOpenAI, model_id: str) -> OpenAIChatCompletionsModel:
    return OpenAIChatCompletionsModel(model=model_id, openai_client=client)


def researcher_instructions() -> str:
    return """You are the **Researcher** on a demo betting desk (not real money).

Your job is to bring back what’s on the board: matches and prices. Use the tool that lists demo matches once, then summarize in plain language what matters (who plays, the prices, which side the market leans toward).

Do not place bets or check balances — that comes later."""


def analyst_instructions() -> str:
    return """You are the **Analyst** on the same demo desk (not real money).

You receive the Researcher’s notes. Give a clear recommendation: where you’d put money in this demo, how much (stake at most 50 in demo units), and why in sentences a business person can follow.

At the end, include short lines the next step can use (match id, pick home/draw/away, stake, odds, whether you’re on the favorite side, and your reason)."""


def decision_instructions() -> str:
    return f"""You are the **Betting** step — you actually submit the demo bet (not real money).

Use the demo wallet name **{DEMO_ACCOUNT}** when the tools ask for an account.

Read the Analyst’s message, place the bet they describe, then confirm the new balance. Reply in plain language: what we backed, how much, and why — plus the updated balance."""


def coordinator_instructions() -> str:
    return f"""You run the demo betting flow for **{DEMO_ACCOUNT}** (not real money).

Work in order:
1. **Researcher** — what’s available and how the market looks.
2. **Analyst** — where we should play and why.
3. **Betting** — place that demo bet and confirm.

Then give the user a short, confident summary: recommendation, stake, and balance — no jargon about tools or APIs."""


def build_researcher_agent(betting: MCPServerStdio, model: OpenAIChatCompletionsModel) -> Agent:
    return Agent(
        name="Researcher",
        instructions=researcher_instructions(),
        model=model,
        mcp_servers=[betting],
        model_settings=ModelSettings(tool_choice="auto"),
    )


def build_analyst_agent(model: OpenAIChatCompletionsModel) -> Agent:
    return Agent(
        name="Analyst",
        instructions=analyst_instructions(),
        model=model,
        model_settings=ModelSettings(tool_choice="auto"),
    )


def build_decision_agent(betting: MCPServerStdio, model: OpenAIChatCompletionsModel) -> Agent:
    return Agent(
        name="Decision",
        instructions=decision_instructions(),
        model=model,
        mcp_servers=[betting],
        model_settings=ModelSettings(tool_choice="auto"),
    )


async def build_betting_coordinator(
    betting: MCPServerStdio,
    *,
    model: OpenAIChatCompletionsModel,
) -> Agent:
    researcher = build_researcher_agent(betting, model)
    researcher_tool = researcher.as_tool(
        tool_name="Researcher",
        tool_description="Looks up current demo matches and prices for this session.",
        max_turns=14,
    )

    analyst = build_analyst_agent(model)
    analyst_tool = analyst.as_tool(
        tool_name="Analyst",
        tool_description="Turns the market picture into a recommendation and rationale.",
        max_turns=14,
    )

    decision = build_decision_agent(betting, model)
    decision_tool = decision.as_tool(
        tool_name="Decision",
        tool_description="Places the demo bet and confirms balance for this session.",
        max_turns=22,
    )

    return Agent(
        name="BettingCoordinator",
        instructions=coordinator_instructions(),
        model=model,
        tools=[researcher_tool, analyst_tool, decision_tool],
        model_settings=ModelSettings(tool_choice="auto"),
    )


async def run_betting_pipeline(
    *,
    openrouter_client: AsyncOpenAI,
    model_id: str,
    mcp_params: dict[str, Any],
    mcp_timeout: float = 120.0,
    max_turns: int = DEFAULT_MAX_TURNS,
) -> Any:
    """Connect MCP, run the coordinator. Demo account and style are fixed in this module."""
    model = make_openrouter_model(openrouter_client, model_id)
    user_msg = (
        "Run research, then analysis, then place one demo bet for this session. "
        f"Follow our usual tone: {DEMO_STYLE}"
    )

    async with AsyncExitStack() as stack:
        betting = await stack.enter_async_context(
            MCPServerStdio(params=mcp_params, client_session_timeout_seconds=mcp_timeout)
        )
        coordinator = await build_betting_coordinator(betting, model=model)
        with trace(f"demo-bet-{DEMO_ACCOUNT}"):
            return await Runner.run(coordinator, user_msg, max_turns=max_turns)
