from contextlib import AsyncExitStack
from accounts_client import read_accounts_resource, read_strategy_resource
from tracers import make_trace_id
from agents import Agent, Tool, Runner, OpenAIChatCompletionsModel, trace
from openai import AsyncOpenAI
from dotenv import load_dotenv
import os
import json
from agents.mcp import MCPServerStdio
from templates import (
    researcher_instructions,
    strategist_instructions,
    risk_manager_instructions,
    trader_instructions,
    trade_message,
    rebalance_message,
    risk_manager_message,
    research_tool,
    strategist_tool,
)
from mcp_params import (
    trader_mcp_server_params,
    researcher_mcp_server_params,
    risk_manager_mcp_server_params,
)

load_dotenv(override=True)

deepseek_api_key = os.getenv("DEEPSEEK_API_KEY")
google_api_key = os.getenv("GOOGLE_API_KEY")
grok_api_key = os.getenv("GROK_API_KEY")
openrouter_api_key = os.getenv("OPENROUTER_API_KEY")

DEEPSEEK_BASE_URL = "https://api.deepseek.com/v1"
GROK_BASE_URL = "https://api.x.ai/v1"
GEMINI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai/"
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

MAX_TURNS = 40  # increased to accommodate the longer 4-step execution sequence

openrouter_client = AsyncOpenAI(base_url=OPENROUTER_BASE_URL, api_key=openrouter_api_key)
deepseek_client = AsyncOpenAI(base_url=DEEPSEEK_BASE_URL, api_key=deepseek_api_key)
grok_client = AsyncOpenAI(base_url=GROK_BASE_URL, api_key=grok_api_key)
gemini_client = AsyncOpenAI(base_url=GEMINI_BASE_URL, api_key=google_api_key)


def get_model(model_name: str):
    if "/" in model_name:
        return OpenAIChatCompletionsModel(model=model_name, openai_client=openrouter_client)
    elif "deepseek" in model_name:
        return OpenAIChatCompletionsModel(model=model_name, openai_client=deepseek_client)
    elif "grok" in model_name:
        return OpenAIChatCompletionsModel(model=model_name, openai_client=grok_client)
    elif "gemini" in model_name:
        return OpenAIChatCompletionsModel(model=model_name, openai_client=gemini_client)
    else:
        return model_name


# Tool builders

async def get_researcher_tool(mcp_servers, model_name) -> Tool:
    researcher = Agent(
        name="Researcher",
        instructions=researcher_instructions(),
        model=get_model(model_name),
        mcp_servers=mcp_servers,
    )
    return researcher.as_tool(tool_name="Researcher", tool_description=research_tool())


async def get_strategist_tool(model_name) -> Tool:
    """Strategist runs as a pure-LLM tool (no MCP servers needed — reasoning only)."""
    strategist = Agent(
        name="Strategist",
        instructions=strategist_instructions(),
        model=get_model(model_name),
    )
    return strategist.as_tool(tool_name="Strategist", tool_description=strategist_tool())


# Risk Manager Agent 

class RiskManager:
    """Standalone Risk Manager agent. Runs independently of the Execution Trader."""

    def __init__(self, name: str, model_name: str = "gpt-4o-mini"):
        self.name = name
        self.model_name = model_name

    async def run_agent(self, risk_mcp_servers):
        from accounts_client import read_accounts_resource
        import json

        account_raw = await read_accounts_resource(self.name)
        account_json = json.loads(account_raw)
        account_json.pop("portfolio_value_time_series", None)
        account = json.dumps(account_json)

        agent = Agent(
            name=f"RiskManager-{self.name}",
            instructions=risk_manager_instructions(self.name),
            model=get_model(self.model_name),
            mcp_servers=risk_mcp_servers,
        )
        message = risk_manager_message(self.name, account)
        await Runner.run(agent, message, max_turns=15)

    async def run_with_mcp_servers(self):
        async with AsyncExitStack() as stack:
            risk_mcp_servers = [
                await stack.enter_async_context(
                    MCPServerStdio(params, client_session_timeout_seconds=120)
                )
                for params in risk_manager_mcp_server_params
            ]
            await self.run_agent(risk_mcp_servers)

    async def run_with_trace(self):
        trace_id = make_trace_id(f"{self.name.lower()}")
        with trace(f"{self.name}-risk-check", trace_id=trace_id):
            await self.run_with_mcp_servers()

    async def run(self):
        try:
            await self.run_with_trace()
        except Exception as e:
            print(f"Error running risk manager for {self.name}: {e}")


# Execution Trader 

class Trader:
    def __init__(self, name: str, lastname="Trader", model_name="gpt-4o-mini"):
        self.name = name
        self.lastname = lastname
        self.agent = None
        self.model_name = model_name
        self.do_trade = True

    async def create_agent(self, trader_mcp_servers, researcher_mcp_servers) -> Agent:
        researcher_tool = await get_researcher_tool(researcher_mcp_servers, self.model_name)
        strat_tool = await get_strategist_tool(self.model_name)

        self.agent = Agent(
            name=self.name,
            instructions=trader_instructions(self.name),
            model=get_model(self.model_name),
            tools=[researcher_tool, strat_tool],
            mcp_servers=trader_mcp_servers,  # includes risk_server for circuit breaker check
        )
        return self.agent

    async def get_account_report(self) -> str:
        account = await read_accounts_resource(self.name)
        account_json = json.loads(account)
        account_json.pop("portfolio_value_time_series", None)
        return json.dumps(account_json)

    async def run_agent(self, trader_mcp_servers, researcher_mcp_servers):
        self.agent = await self.create_agent(trader_mcp_servers, researcher_mcp_servers)
        account = await self.get_account_report()
        strategy = await read_strategy_resource(self.name)
        message = (
            trade_message(self.name, strategy, account)
            if self.do_trade
            else rebalance_message(self.name, strategy, account)
        )
        await Runner.run(self.agent, message, max_turns=MAX_TURNS)

    async def run_with_mcp_servers(self):
        async with AsyncExitStack() as stack:
            trader_mcp_servers = [
                await stack.enter_async_context(
                    MCPServerStdio(params, client_session_timeout_seconds=120)
                )
                for params in trader_mcp_server_params
            ]
            async with AsyncExitStack() as stack:
                researcher_mcp_servers = [
                    await stack.enter_async_context(
                        MCPServerStdio(params, client_session_timeout_seconds=120)
                    )
                    for params in researcher_mcp_server_params(self.name)
                ]
                await self.run_agent(trader_mcp_servers, researcher_mcp_servers)

    async def run_with_trace(self):
        trace_name = f"{self.name}-trading" if self.do_trade else f"{self.name}-rebalancing"
        trace_id = make_trace_id(f"{self.name.lower()}")
        with trace(trace_name, trace_id=trace_id):
            await self.run_with_mcp_servers()

    async def run(self):
        try:
            await self.run_with_trace()
        except Exception as e:
            print(f"Error running trader {self.name}: {e}")
        self.do_trade = not self.do_trade
