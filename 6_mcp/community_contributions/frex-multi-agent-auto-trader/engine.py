import os
import json
import asyncio
import sys
from typing import List, Optional
from contextlib import AsyncExitStack

import mcp
from mcp.client.stdio import stdio_client
from mcp import StdioServerParameters
from dotenv import load_dotenv
from openai import AsyncOpenAI

from agents import Agent, Tool, Runner, OpenAIChatCompletionsModel, trace, add_trace_processor, FunctionTool
from agents.mcp import MCPServerStdio

from backend import Account, is_market_open, LogTracer, make_trace_id, reset_risk
from config import (
    researcher_instructions, strategist_instructions, risk_manager_instructions,
    trader_instructions, trade_message, rebalance_message, risk_manager_message,
    research_tool, strategist_tool, trader_mcp_server_params, 
    researcher_mcp_server_params, risk_manager_mcp_server_params
)

load_dotenv(override=True)

# Global config
RUN_EVERY_N_MINUTES = int(os.getenv("RUN_EVERY_N_MINUTES", "60"))
RUN_EVEN_WHEN_MARKET_IS_CLOSED = os.getenv("RUN_EVEN_WHEN_MARKET_IS_CLOSED", "false").lower() == "true"
USE_MANY_MODELS = os.getenv("USE_MANY_MODELS", "false").lower() == "true"
MAX_TURNS = 20

# Model Mapping
NAMES = ["Warren", "George", "Ray", "Cathie"]
LASTNAMES = ["Patience", "Bold", "Systematic", "Crypto"]

if USE_MANY_MODELS:
    MODEL_NAMES = ["gpt-4o-mini", "deepseek-chat", "gemini-2.0-flash-exp", "grok-beta"]
    SHORT_MODEL_NAMES = ["GPT 4o Mini", "DeepSeek V3", "Gemini 2.0", "Grok Beta"]
else:
    MODEL_NAMES = ["gpt-4o-mini"] * 4
    SHORT_MODEL_NAMES = ["GPT 4o mini"] * 4

# Accounts client
ACCOUNTS_PARAMS = StdioServerParameters(command="uv", args=["run", "servers.py", "accounts"], env=None)


def _mcp_stdio_agent_params(p: StdioServerParameters) -> dict:
    """MCPServerStdio expects a param mapping (TypedDict), not mcp.StdioServerParameters."""
    return p.model_dump()

async def read_accounts_resource(name: str):
    async with stdio_client(ACCOUNTS_PARAMS) as streams:
        async with mcp.ClientSession(*streams) as session:
            await session.initialize()
            result = await session.read_resource(f"accounts://accounts_server/{name}")
            return result.contents[0].text

async def read_strategy_resource(name: str):
    async with stdio_client(ACCOUNTS_PARAMS) as streams:
        async with mcp.ClientSession(*streams) as session:
            await session.initialize()
            result = await session.read_resource(f"accounts://strategy/{name}")
            return result.contents[0].text

# Agent classes
class Trader:
    def __init__(self, name: str, lastname: str, model_name: str, do_trade: bool = True):
        self.name = name
        self.lastname = lastname
        self.model_name = model_name
        self.do_trade = do_trade
        
        # Determine Base URL based on provider
        base_url = "https://api.openai.com/v1"
        api_key = os.getenv("OPENAI_API_KEY")
        
        if "deepseek" in model_name:
            base_url, api_key = "https://api.deepseek.com/v1", os.getenv("DEEPSEEK_API_KEY")
        elif "gemini" in model_name:
            base_url, api_key = "https://generativelanguage.googleapis.com/v1beta/openai/", os.getenv("GOOGLE_API_KEY")
        elif "grok" in model_name:
            base_url, api_key = "https://api.x.ai/v1", os.getenv("GROK_API_KEY")

        self.model = OpenAIChatCompletionsModel(model=model_name, openai_client=AsyncOpenAI(api_key=api_key, base_url=base_url))
        self.agent = Agent(
            name=f"{self.name} {self.lastname}",
            instructions=trader_instructions(),
            model=self.model,
            tools=[research_tool, strategist_tool]
        )

    async def run_agent(self, trader_mcp, researcher_mcp):
        account = await read_accounts_resource(self.name)
        strategy = await read_strategy_resource(self.name)
         
        self.agent.tools[:] = [research_tool, strategist_tool]
        self.agent.mcp_servers[:] = [*trader_mcp, *researcher_mcp]
        
        msg = trade_message(self.name, strategy, account) if self.do_trade else rebalance_message(self.name, strategy, account)
        await Runner.run(self.agent, msg, max_turns=MAX_TURNS)

    async def run(self):
        trace_name = f"{self.name}-{'trading' if self.do_trade else 'rebalancing'}"
        trace_id = make_trace_id(self.name.lower())
        
        try:
            with trace(trace_name, trace_id=trace_id):
                async with AsyncExitStack() as stack:
                    t_mcp = [
                        await stack.enter_async_context(MCPServerStdio(_mcp_stdio_agent_params(p)))
                        for p in trader_mcp_server_params
                    ]
                    r_mcp = [
                        await stack.enter_async_context(MCPServerStdio(_mcp_stdio_agent_params(p)))
                        for p in researcher_mcp_server_params(self.name)
                    ]
                    await self.run_agent(t_mcp, r_mcp)
        except Exception as e:
            print(f"Error running trader {self.name}: {e}")

class RiskManager:
    def __init__(self, name: str, model_name: str):
        self.name = name
        self.model = OpenAIChatCompletionsModel(model=model_name, openai_client=AsyncOpenAI())
        self.agent = Agent(
            name=f"Risk Manager for {name}",
            instructions=risk_manager_instructions(),
            model=self.model
        )

    async def run(self):
        trace_id = make_trace_id(f"{self.name.lower()}risk")
        try:
            with trace(f"{self.name}-risk-assessment", trace_id=trace_id):
                async with AsyncExitStack() as stack:
                    r_mcp = [
                        await stack.enter_async_context(MCPServerStdio(_mcp_stdio_agent_params(p)))
                        for p in risk_manager_mcp_server_params
                    ]
                    self.agent.mcp_servers[:] = r_mcp
                    
                    account = await read_accounts_resource(self.name)
                    await Runner.run(self.agent, risk_manager_message(self.name, account), max_turns=MAX_TURNS)
        except Exception as e:
            print(f"Error running risk manager for {self.name}: {e}")

# Reset
STRATEGIES = {
    "Warren": "Value-oriented investor, identifies high-quality companies trading below intrinsic value. Long-term focus.",
    "George": "Aggressive macro trader. Seeks market mispricings and geopolitical imbalances. Contrarian approach.",
    "Ray": "Systematic, principles-based approach. Diversified across asset classes using risk parity.",
    "Cathie": "Aggressive innovation focus, specifically Crypto ETFs and disruptive technology."
}

def reset_traders():
    for name in NAMES:
        strategy = STRATEGIES.get(name, "Balanced trading strategy.")
        Account.get(name).reset(strategy)
        reset_risk(name)
        print(f"Reset account and risk state for {name}")

# Trading floor
async def run_cycle(traders: List[Trader], risk_managers: List[RiskManager]):
    print("Phase 1: Risk assessment...")
    await asyncio.gather(*[rm.run() for rm in risk_managers])
    print("Phase 2: Execution trading...")
    await asyncio.gather(*[t.run() for t in traders])

async def main_loop():
    add_trace_processor(LogTracer())
    traders = [Trader(n, l, m) for n, l, m in zip(NAMES, LASTNAMES, MODEL_NAMES)]
    risk_managers = [RiskManager(n, m) for n, m in zip(NAMES, MODEL_NAMES)]

    while True:
        if RUN_EVEN_WHEN_MARKET_IS_CLOSED or is_market_open():
            await run_cycle(traders, risk_managers)
        else:
            print("Market closed. Skipping.")
        await asyncio.sleep(RUN_EVERY_N_MINUTES * 60)

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "reset":
        reset_traders()
    else:
        asyncio.run(main_loop())