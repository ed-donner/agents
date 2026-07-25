import json
from contextlib import AsyncExitStack

from accounts_client import read_accounts_resource, read_strategy_resource
from agents import Agent, Runner, Tool, trace
from agents.mcp import MCPServerStdio
from crypto_tracers import make_trace_id
from dotenv import load_dotenv
from mcp_params import researcher_mcp_server_params, trader_mcp_server_params
from templates import (
    rebalance_message,
    research_tool,
    researcher_instructions,
    trade_message,
    trader_instructions,
)

load_dotenv(override=True)

MAX_TURNS = 30


async def get_researcher(mcp_servers, model_name: str) -> Agent:
    return Agent(
        name="Researcher",
        instructions=researcher_instructions(),
        model=model_name,
        mcp_servers=mcp_servers,
    )


async def get_researcher_tool(mcp_servers, model_name: str) -> Tool:
    researcher = await get_researcher(mcp_servers, model_name)
    return researcher.as_tool(tool_name="Researcher", tool_description=research_tool())


class Trader:
    def __init__(self, name: str, lastname="Trader", model_name="gpt-4o-mini"):
        self.name = name
        self.lastname = lastname
        self.agent = None
        self.model_name = model_name
        self.do_trade = True

    async def create_agent(self, trader_mcp_servers, researcher_mcp_servers) -> Agent:
        tool = await get_researcher_tool(researcher_mcp_servers, self.model_name)
        self.agent = Agent(
            name=self.name,
            instructions=trader_instructions(self.name),
            model=self.model_name,
            tools=[tool],
            mcp_servers=trader_mcp_servers,
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
            async with AsyncExitStack() as rstack:
                researcher_mcp_servers = [
                    await rstack.enter_async_context(
                        MCPServerStdio(params, client_session_timeout_seconds=120)
                    )
                    for params in researcher_mcp_server_params(self.name)
                ]
                await self.run_agent(trader_mcp_servers, researcher_mcp_servers)

    async def run_with_trace(self):
        trace_name = f"{self.name}-crypto-trading" if self.do_trade else f"{self.name}-crypto-rebalancing"
        trace_id = make_trace_id(self.name.lower())
        with trace(trace_name, trace_id=trace_id):
            await self.run_with_mcp_servers()

    async def run(self):
        try:
            await self.run_with_trace()
        except Exception as e:
            print(f"Error running trader {self.name}: {e}")
        self.do_trade = not self.do_trade
