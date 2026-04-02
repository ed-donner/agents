from contextlib import AsyncExitStack
import json
import os
import sys
from pathlib import Path

# This folder must win over `6_mcp/` on sys.path so we import *this* `mcp_params.py`, not
# `6_mcp/mcp_params.py` (uv run does not always put the script dir first).
_CONTRIB_DIR = Path(__file__).resolve().parent
if str(_CONTRIB_DIR) not in sys.path:
    sys.path.insert(0, str(_CONTRIB_DIR))

ROOT_6_MCP = Path(__file__).resolve().parents[2]
if str(ROOT_6_MCP) not in sys.path:
    sys.path.append(str(ROOT_6_MCP))

from accounts_client import read_accounts_resource, read_strategy_resource
from agents import (
    Agent,
    ModelSettings,
    OpenAIChatCompletionsModel,
    RunConfig,
    Runner,
    Tool,
    trace,
)
from agents.mcp import MCPServerStdio
from dotenv import load_dotenv
from openai import AsyncOpenAI
from tracers import make_trace_id

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
AGENT_MODEL_SETTINGS = ModelSettings(max_tokens=1024, temperature=0.3)

openrouter_api_key = os.getenv("OPENROUTER_API_KEY")
groq_api_key = os.getenv("GROQ_API_KEY")
cerebras_api_key = os.getenv("CEREBRAS_API_KEY")

openrouter_client = AsyncOpenAI(
    base_url="https://openrouter.ai/api/v1", api_key=openrouter_api_key, max_retries=0
)
groq_client = AsyncOpenAI(
    base_url="https://api.groq.com/openai/v1", api_key=groq_api_key, max_retries=0
)
cerebras_client = AsyncOpenAI(
    base_url="https://api.cerebras.ai/v1", api_key=cerebras_api_key, max_retries=0
)


def _default_trader_model() -> str:
    if groq_api_key:
        return "llama-3.3-70b-versatile"
    if cerebras_api_key:
        return "qwen-3-235b-a22b-instruct-2507"
    return "qwen/qwen-2.5-72b-instruct"


def _is_retryable_model_error(error: Exception) -> bool:
    msg = str(error).lower()
    retry_markers = [
        "error code: 429",
        "error code: 402",
        "rate limit",
        "insufficient credits",
        "timeout",
        "apitimeouterror",
    ]
    return any(marker in msg for marker in retry_markers)


def _candidate_models(primary_model: str) -> list[str]:
    candidates = [primary_model]
    if groq_api_key:
        for name in ("llama-3.3-70b-versatile", "llama-3.1-8b-instant"):
            if name not in candidates:
                candidates.append(name)
    if cerebras_api_key:
        for name in ("qwen-3-235b-a22b-instruct-2507",):
            if name not in candidates:
                candidates.append(name)
    if openrouter_api_key:
        for name in ("qwen/qwen-2.5-72b-instruct", "meta-llama/llama-3.3-70b-instruct"):
            if name not in candidates:
                candidates.append(name)
    return candidates


def get_model(model_name: str):
    if "/" in model_name:
        return OpenAIChatCompletionsModel(model=model_name, openai_client=openrouter_client)
    if cerebras_api_key and model_name.startswith("qwen-3"):
        return OpenAIChatCompletionsModel(model=model_name, openai_client=cerebras_client)
    if groq_api_key and not model_name.startswith(("gpt-", "o1", "o3", "chatgpt-")):
        return OpenAIChatCompletionsModel(model=model_name, openai_client=groq_client)
    return model_name


async def get_researcher(mcp_servers, model_name) -> Agent:
    return Agent(
        name="Researcher",
        instructions=researcher_instructions(),
        model=get_model(model_name),
        model_settings=AGENT_MODEL_SETTINGS,
        mcp_servers=mcp_servers,
    )


async def get_researcher_tool(mcp_servers, model_name) -> Tool:
    researcher = await get_researcher(mcp_servers, model_name)
    return researcher.as_tool(tool_name="Researcher", tool_description=research_tool())


class Trader:
    def __init__(self, name: str, lastname="Trader", model_name: str | None = None):
        self.name = name
        self.lastname = lastname
        self.agent = None
        self.model_name = model_name or os.getenv("TRADER_MODEL") or _default_trader_model()
        self.do_trade = True

    async def create_agent(self, trader_mcp_servers, researcher_mcp_servers) -> Agent:
        tool = await get_researcher_tool(researcher_mcp_servers, self.model_name)
        self.agent = Agent(
            name=self.name,
            instructions=trader_instructions(self.name),
            model=get_model(self.model_name),
            model_settings=AGENT_MODEL_SETTINGS,
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
        account = await self.get_account_report()
        strategy = await read_strategy_resource(self.name)
        message = (
            trade_message(self.name, strategy, account)
            if self.do_trade
            else rebalance_message(self.name, strategy, account)
        )
        last_error: Exception | None = None
        for candidate in _candidate_models(self.model_name):
            try:
                self.model_name = candidate
                self.agent = await self.create_agent(trader_mcp_servers, researcher_mcp_servers)
                await Runner.run(
                    self.agent,
                    message,
                    max_turns=MAX_TURNS,
                    run_config=RunConfig(model_settings=AGENT_MODEL_SETTINGS),
                )
                return
            except Exception as e:
                last_error = e
                print(f"Model failed for trader {self.name}: {candidate} -> {e}")
                if not _is_retryable_model_error(e):
                    raise
                print(f"Trying fallback model for trader {self.name}...")
        if last_error:
            raise last_error

    async def run_with_mcp_servers(self):
        async with AsyncExitStack() as stack:
            trader_mcp_servers = [
                await stack.enter_async_context(
                    MCPServerStdio(params, client_session_timeout_seconds=120)
                )
                for params in trader_mcp_server_params
            ]
            async with AsyncExitStack() as stack2:
                researcher_mcp_servers = [
                    await stack2.enter_async_context(
                        MCPServerStdio(params, client_session_timeout_seconds=120)
                    )
                    for params in researcher_mcp_server_params(self.name)
                ]
                await self.run_agent(trader_mcp_servers, researcher_mcp_servers)

    async def run_with_trace(self):
        trace_name = f"{self.name}-trading" if self.do_trade else f"{self.name}-rebalancing"
        trace_id = make_trace_id(self.name.lower())
        with trace(trace_name, trace_id=trace_id):
            await self.run_with_mcp_servers()

    async def run(self):
        try:
            await self.run_with_trace()
        except Exception as e:
            print(f"Error running trader {self.name}: {e}")
        self.do_trade = not self.do_trade
