from contextlib import AsyncExitStack
from accounts_client import read_accounts_resource, read_strategy_resource
from tracers import make_trace_id
from agents import Agent, Tool, Runner, OpenAIChatCompletionsModel, trace
from openai import AsyncOpenAI
from dotenv import load_dotenv
import os
import json
from agents.mcp import MCPServerStdio
from database import write_log
from templates import researcher_instructions, trader_instructions, trade_message, rebalance_message, research_tool
from mcp_params import trader_mcp_server_params, researcher_mcp_server_params

load_dotenv(override=True)

deepseek_api_key = os.getenv("DEEPSEEK_API_KEY")
google_api_key = os.getenv("GOOGLE_API_KEY")
grok_api_key = os.getenv("GROK_API_KEY")
openrouter_api_key = os.getenv("OPENROUTER_API_KEY")

DEEPSEEK_BASE_URL = "https://api.deepseek.com/v1"
GROK_BASE_URL = "https://api.x.ai/v1"
GEMINI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai/"
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

MAX_TURNS = 30

openrouter_client = AsyncOpenAI(base_url=OPENROUTER_BASE_URL, api_key=openrouter_api_key)
deepseek_client = AsyncOpenAI(base_url=DEEPSEEK_BASE_URL, api_key=deepseek_api_key)
grok_client = AsyncOpenAI(base_url=GROK_BASE_URL, api_key=grok_api_key)
gemini_client = AsyncOpenAI(base_url=GEMINI_BASE_URL, api_key=google_api_key)


def get_model(model_name: str):
    if "/" in model_name:
        return OpenAIChatCompletionsModel(model=model_name, openai_client=openrouter_client)
    if "deepseek" in model_name:
        return OpenAIChatCompletionsModel(model=model_name, openai_client=deepseek_client)
    if "grok" in model_name:
        return OpenAIChatCompletionsModel(model=model_name, openai_client=grok_client)
    if "gemini" in model_name:
        return OpenAIChatCompletionsModel(model=model_name, openai_client=gemini_client)
    return model_name


async def _get_researcher_tool(mcp_servers, model_name: str) -> Tool:
    researcher = Agent(
        name="Researcher",
        instructions=researcher_instructions(),
        model=get_model(model_name),
        mcp_servers=mcp_servers,
    )
    return researcher.as_tool(tool_name="Researcher", tool_description=research_tool())


class TraderAgent:
    """Agent runner — responsible for running the LLM-powered trading agent."""

    def __init__(self, name: str, lastname: str = "Trader", model_name: str = "gpt-4.1-mini"):
        self.name = name
        self.lastname = lastname
        self.model_name = model_name
        self._do_trade = True  # alternates trade / rebalance each run

    async def _create_agent(self, trader_mcp_servers, researcher_mcp_servers) -> Agent:
        researcher_tool = await _get_researcher_tool(researcher_mcp_servers, self.model_name)
        return Agent(
            name=self.name,
            instructions=trader_instructions(self.name),
            model=get_model(self.model_name),
            tools=[researcher_tool],
            mcp_servers=trader_mcp_servers,
        )

    async def _get_account_report(self) -> str:
        account = await read_accounts_resource(self.name)
        data = json.loads(account)
        data.pop("portfolio_value_time_series", None)
        return json.dumps(data)

    async def _run_agent(self, trader_mcp_servers, researcher_mcp_servers) -> None:
        agent = await self._create_agent(trader_mcp_servers, researcher_mcp_servers)
        account = await self._get_account_report()
        strategy = await read_strategy_resource(self.name)
        message = (
            trade_message(self.name, strategy, account)
            if self._do_trade
            else rebalance_message(self.name, strategy, account)
        )
        await Runner.run(agent, message, max_turns=MAX_TURNS)

    async def _run_with_mcp_servers(self) -> None:
        async with AsyncExitStack() as trader_stack:
            trader_servers = [
                await trader_stack.enter_async_context(
                    MCPServerStdio(params, client_session_timeout_seconds=120)
                )
                for params in trader_mcp_server_params
            ]
            async with AsyncExitStack() as researcher_stack:
                researcher_servers = [
                    await researcher_stack.enter_async_context(
                        MCPServerStdio(params, client_session_timeout_seconds=120)
                    )
                    for params in researcher_mcp_server_params(self.name)
                ]
                await self._run_agent(trader_servers, researcher_servers)

    async def run(self) -> None:
        """Run one trading cycle (trade or rebalance), log any errors."""
        run_type = "trading" if self._do_trade else "rebalancing"
        trace_id = make_trace_id(self.name.lower())
        try:
            with trace(f"{self.name}-{run_type}", trace_id=trace_id):
                await self._run_with_mcp_servers()
        except Exception as exc:
            error_msg = f"Run failed ({run_type}): {exc}"
            print(f"[{self.name}] {error_msg}")
            write_log(self.name, "agent", error_msg)
        finally:
            # Always flip mode so next call does the opposite
            self._do_trade = not self._do_trade
