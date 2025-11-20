from contextlib import AsyncExitStack
from agents import Agent, Runner, trace, OpenAIChatCompletionsModel
from agents.mcp import MCPServerStdio
from openai import AsyncOpenAI
from dotenv import load_dotenv
import os
import json
from src.utils.templates import risk_manager_instructions, risk_assessment_message
from src.utils.mcp_params import risk_manager_mcp_server_params
from src.agents.accounts import Account
from src.utils.tracers import make_trace_id
from src.database.database import write_risk_assessment, write_log

load_dotenv(override=True)

MAX_TURNS = 20

class RiskManager:
    def __init__(self, trader_names: list[str], model_name="gpt-4o-mini"):
        self.trader_names = trader_names
        self.model_name = model_name
        self.agent = None

    async def create_agent(self, mcp_servers) -> Agent:
        self.agent = Agent(
            name="RiskManager",
            instructions=risk_manager_instructions(),
            model=self.model_name,
            mcp_servers=mcp_servers,
        )
        return self.agent

    def gather_all_accounts_data(self) -> str:
        all_data = {}
        for trader_name in self.trader_names:
            account = Account.get(trader_name)
            account_json = json.loads(account.report())
            account_json.pop("portfolio_value_time_series", None)
            all_data[trader_name] = account_json

        return json.dumps(all_data, indent=2)

    async def run_agent(self, mcp_servers):
        self.agent = await self.create_agent(mcp_servers)
        all_accounts = self.gather_all_accounts_data()
        message = risk_assessment_message(all_accounts)
        result = await Runner.run(self.agent, message, max_turns=MAX_TURNS)
        return result.final_output

    async def run_with_mcp_servers(self):
        async with AsyncExitStack() as stack:
            mcp_servers = [
                await stack.enter_async_context(
                    MCPServerStdio(params, client_session_timeout_seconds=120)
                )
                for params in risk_manager_mcp_server_params
            ]
            result = await self.run_agent(mcp_servers)
            return result

    async def run_with_trace(self):
        trace_name = "risk-assessment"
        trace_id = make_trace_id("riskmanager")
        with trace(trace_name, trace_id=trace_id):
            result = await self.run_with_mcp_servers()
            return result

    async def run(self):
        try:
            write_log("riskmanager", "trace", "Starting risk assessment")
            result = await self.run_with_trace()
            assessment = result[:500] if result else "Assessment completed"
            recommendations = result[500:1000] if len(result) > 500 else "See full assessment"
            write_risk_assessment(assessment, recommendations)
            write_log("riskmanager", "trace", "Risk assessment completed")
            return result
        except Exception as e:
            write_log("riskmanager", "trace", f"Error: {str(e)}")
            print(f"Error running risk manager: {e}")
            return None
