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
    trader_instructions,
    trade_message,
    rebalance_message,
    research_tool,
)
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
    elif "deepseek" in model_name:
        return OpenAIChatCompletionsModel(model=model_name, openai_client=deepseek_client)
    elif "grok" in model_name:
        return OpenAIChatCompletionsModel(model=model_name, openai_client=grok_client)
    elif "gemini" in model_name:
        return OpenAIChatCompletionsModel(model=model_name, openai_client=gemini_client)
    else:
        return model_name


async def get_researcher(mcp_servers, model_name) -> Agent:
    researcher = Agent(
        name="Researcher",
        instructions=researcher_instructions(),
        model=get_model(model_name),
        mcp_servers=mcp_servers,
    )
    return researcher


async def get_researcher_tool(mcp_servers, model_name) -> Tool:
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
            model=get_model(self.model_name),
            tools=[tool],
            mcp_servers=trader_mcp_servers,
        )
        return self.agent

    async def get_account_report(self, accounts_mcp_server=None) -> str:
        """
        Get account report, optionally using a shared MCP server connection.
        
        Args:
            accounts_mcp_server: Optional MCP server connection to reuse (avoids spawning subprocess)
        """
        if accounts_mcp_server:
            # Use shared MCP server connection (efficient)
            result = await accounts_mcp_server.read_resource(
                f"accounts://accounts_server/{self.name}"
            )
            account = result.contents[0].text
        else:
            # Fallback to accounts_client (spawns subprocess)
            account = await read_accounts_resource(self.name)
        
        account_json = json.loads(account)
        account_json.pop("portfolio_value_time_series", None)
        return json.dumps(account_json)
    
    async def get_strategy(self, accounts_mcp_server=None) -> str:
        """
        Get trader strategy, optionally using a shared MCP server connection.
        
        Args:
            accounts_mcp_server: Optional MCP server connection to reuse (avoids spawning subprocess)
        """
        if accounts_mcp_server:
            # Use shared MCP server connection (efficient)
            result = await accounts_mcp_server.read_resource(
                f"accounts://strategy/{self.name}"
            )
            return result.contents[0].text
        else:
            # Fallback to accounts_client (spawns subprocess)
            return await read_strategy_resource(self.name)

    async def run_agent(self, trader_mcp_servers, researcher_mcp_servers):
        """
        Run the trader agent with provided MCP servers.
        
        This method now optimally uses the shared accounts MCP server for
        reading resources instead of spawning temporary subprocesses.
        """
        print(f"[{self.name}] Creating agent...", flush=True)
        self.agent = await self.create_agent(trader_mcp_servers, researcher_mcp_servers)
        
        # Read account and strategy using accounts_client (spawns temporary connections)
        print(f"[{self.name}] Reading account report...", flush=True)
        account = await self.get_account_report()
        print(f"[{self.name}] Reading strategy...", flush=True)
        strategy = await self.get_strategy()
        
        action = "trading" if self.do_trade else "rebalancing"
        print(f"[{self.name}] Preparing {action} message...", flush=True)
        message = (
            trade_message(self.name, strategy, account)
            if self.do_trade
            else rebalance_message(self.name, strategy, account)
        )
        
        print(f"[{self.name}] Starting agent run with message length: {len(message)} chars", flush=True)
        print(f"[{self.name}] Message preview: {message[:200]}...", flush=True)
        
        result = await Runner.run(self.agent, message, max_turns=MAX_TURNS)
        
        print(f"[{self.name}] Agent run completed", flush=True)
        if hasattr(result, 'final_output'):
            print(f"[{self.name}] Final output length: {len(result.final_output) if result.final_output else 0} chars", flush=True)
        
        return result

    async def run_with_shared_servers(self, trader_mcp_servers, researcher_mcp_servers):
        """
        Run trader with pre-created shared MCP servers (orchestrator pattern).
        
        This method accepts existing MCP server connections instead of spawning its own,
        which significantly reduces subprocess overhead when multiple traders run.
        
        Args:
            trader_mcp_servers: Shared trader MCP servers (accounts, push, market)
            researcher_mcp_servers: Trader-specific researcher servers (fetch, brave, memory)
        """
        trace_name = f"{self.name}-trading" if self.do_trade else f"{self.name}-rebalancing"
        trace_id = make_trace_id(f"{self.name.lower()}")
        
        try:
            with trace(trace_name, trace_id=trace_id):
                await self.run_agent(trader_mcp_servers, researcher_mcp_servers)
        except Exception as e:
            print(f"Error running trader {self.name}: {e}")
        
        # Toggle between trading and rebalancing
        self.do_trade = not self.do_trade
