import asyncio
from pathlib import Path
from dotenv import load_dotenv
from agents import Agent, OpenAIChatCompletionsModel, Runner
from agents.mcp import MCPServerStdio
from openai import AsyncOpenAI

load_dotenv(override=True)

openai_client = AsyncOpenAI()

MODEL = "gpt-4.1-mini"

_ROOT = Path(__file__).resolve().parent


def get_model():
    return OpenAIChatCompletionsModel(model=MODEL, openai_client=openai_client)


async def run_crisis():
    print(f"Starting Real Supply Chain Crisis Agent ({MODEL})\n")

    mcp_params = {
        "command": "uv",
        "args": ["run", "supplychain_server.py"],
        "env": None,
        "cwd": str(_ROOT),
    }

    async with MCPServerStdio(mcp_params, client_session_timeout_seconds=120) as mcp_server:
        agent = Agent(
            name="SupplyChainCoordinator",
            instructions="""
                You are the Supply Chain Crisis Coordinator for manufacturing projects.

                When any delay is reported:
                1. First read the live resources: supply://delays and supply://inventory
                2. Use the find_alternative_supplier tool to explore options
                3. Decide on the best mitigation
                4. Store your final decision using the store_memory tool
                (use key format: {part}_mitigation)
                5. Use expedite_shipping only if it makes sense
                6. End with a clear, actionable plan and mention what you stored in memory.

                You have access to Tools, Resources, and the crisis_management prompt.
                Never solve problems by reasoning alone — always use the supplied capabilities.
                """,
            model=get_model(),
            mcp_servers=[mcp_server],
        )

        initial_message = """
        A supply chain disruption has been reported:

        Project: PROJECT-001
        Part: SCREW_X is delayed by 5 days.

        Resolve this disruption using all available capabilities.
        Show your full reasoning and tool usage.
        """

        result = await Runner.run(
            starting_agent=agent,
            input=initial_message,
            max_turns=20,
        )

    print("\n" + "=" * 70)
    print("FINAL AGENT OUTPUT:")
    print("=" * 70)
    print(result.final_output)
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(run_crisis())
