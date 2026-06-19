# traders.py
from contextlib import AsyncExitStack
from accounts_client import read_accounts_resource, read_strategy_resource
from tracers import make_trace_id
from agents import Agent, Tool, Runner, OpenAIChatCompletionsModel, trace
from openai import AsyncOpenAI
from dotenv import load_dotenv
import os
import json
import traceback
from agents.mcp import MCPServerStdio
from templates import (
    researcher_instructions,
    trader_instructions,
    trade_message,
    rebalance_message,
    research_tool,
)
from mcp_params import trader_mcp_server_params, researcher_mcp_server_params

# Anthropic shim and SDK
from anthropic import AsyncAnthropic
from openai_compat_anthropic import OpenAICompatAnthropicClient

# ✅ NEW: Gemini shim
from openai_compat_gemini import GeminiCompatOpenAIClient

load_dotenv(override=True)

deepseek_api_key = os.getenv("DEEPSEEK_API_KEY")
google_api_key = os.getenv("GOOGLE_API_KEY")
grok_api_key = os.getenv("GROK_API_KEY")
openrouter_api_key = os.getenv("OPENROUTER_API_KEY")
groq_api_key = os.getenv("GROQ_API_KEY")
anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")

DEEPSEEK_BASE_URL = "https://api.deepseek.com/v1"
GROK_BASE_URL = "https://api.x.ai/v1"
GEMINI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai/"
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
GROQ_BASE_URL = "https://api.groq.com/openai/v1"

MAX_TURNS = 30

openrouter_client = AsyncOpenAI(base_url=OPENROUTER_BASE_URL, api_key=openrouter_api_key)
deepseek_client = AsyncOpenAI(base_url=DEEPSEEK_BASE_URL, api_key=deepseek_api_key)
grok_client = AsyncOpenAI(base_url=GROK_BASE_URL, api_key=grok_api_key)

# ❌ OLD:
# gemini_client = AsyncOpenAI(base_url=GEMINI_BASE_URL, api_key=google_api_key)
# ✅ NEW: wrap Gemini with compat shim (adds retries and cleans unsupported params)
raw_gemini_client = AsyncOpenAI(base_url=GEMINI_BASE_URL, api_key=google_api_key)
gemini_client = GeminiCompatOpenAIClient(raw_gemini_client)

groq_client = AsyncOpenAI(base_url=GROQ_BASE_URL, api_key=groq_api_key)
anthropic_client = AsyncAnthropic(api_key=anthropic_api_key)

def get_model(model_name: str):
    # Keep returning the identifier at construction time (serializer-safe)
    return model_name

def instantiate_model_from_name(model_name: str):
    print("[DEBUG] instantiate_model_from_name: start:", model_name)
    name = (model_name or "").lower()

    if "/" in model_name:
        return OpenAIChatCompletionsModel(model=model_name, openai_client=openrouter_client)
    if "deepseek" in name:
        return OpenAIChatCompletionsModel(model=model_name, openai_client=deepseek_client)
    if "llama" in name or "groq" in name:
        return OpenAIChatCompletionsModel(model=model_name, openai_client=groq_client)

    # ✅ Gemini via shim
    if "gemini" in name:
        return OpenAIChatCompletionsModel(model=model_name, openai_client=gemini_client)

    # ✅ Claude via Anthropic shim
    if "claude" in name:
        anth_client = AsyncAnthropic(api_key=anthropic_api_key)
        shim_client = OpenAICompatAnthropicClient(anth_client)
        print(
            "[DEBUG] Shim client config:",
            getattr(shim_client, "api_key", None),
            getattr(shim_client, "base_url", None)
        )
        return OpenAIChatCompletionsModel(model=model_name, openai_client=shim_client)

    # Default: string (GPT etc.)
    return model_name

async def get_researcher(mcp_servers, model_name) -> Agent:
    model_with_overrides = model_name  # keep plain
    return Agent(
        name="Researcher",
        instructions=researcher_instructions(),
        model=get_model(model_with_overrides),
        mcp_servers=mcp_servers,
    )

async def get_researcher_tool(mcp_servers, model_name) -> Tool:
    researcher = await get_researcher(mcp_servers, model_name)
    researcher.model = instantiate_model_from_name(model_name)
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

        print("[DEBUG] Before instantiation:", self.agent.model)
        runtime_model = instantiate_model_from_name(self.model_name)
        self.agent.model = runtime_model
        print("[DEBUG] After instantiation:", self.agent.model, type(self.agent.model))

        if self.do_trade:
            turn_cap = 10    # executing trades
        else:
            turn_cap = 6    # rebalance / lighter loop
        
        print(f"[DEBUG] Trader turn_cap={turn_cap} model={self.model_name} do_trade={self.do_trade}")
        
        await Runner.run(self.agent, message, max_turns=turn_cap)

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
            traceback.print_exc()
        self.do_trade = not self.do_trade
