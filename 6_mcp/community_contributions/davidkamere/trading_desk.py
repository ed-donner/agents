import asyncio
import json
import requests
import os
import sys
from contextlib import AsyncExitStack
from pathlib import Path
from typing import Any

import pandas as pd
from agents import Agent, Runner, Tool, OpenAIChatCompletionsModel, function_tool
from agents.mcp import MCPServerStdio
from dotenv import load_dotenv
from openai import AsyncOpenAI

from desk_database import (
    init_db,
    log_desk_review,
    log_risk_alert,
    log_trader_action,
    read_recent_actions,
    read_recent_alerts,
    read_recent_reviews,
)
from templates import (
    portfolio_manager_instructions,
    research_tool_description,
    researcher_instructions,
    risk_officer_instructions,
    trader_instructions,
    trader_message,
)

BASE_DIR = Path(__file__).parent
PROJECT_ROOT = BASE_DIR.parents[1]
if str(PROJECT_ROOT) in sys.path:
    sys.path.remove(str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT))
if str(BASE_DIR) in sys.path:
    sys.path.remove(str(BASE_DIR))
sys.path.append(str(BASE_DIR))

from accounts import Account  # noqa: E402
from reset import waren_strategy, cathie_strategy  # noqa: E402

load_dotenv(override=True)

OPENROUTER_API_KEY = os.getenv('OPENROUTER_API_KEY')
OPENROUTER_MODEL = os.getenv('OPENROUTER_MODEL', 'openai/gpt-4o-mini')
SERPER_API_KEY = os.getenv('SERPER_API_KEY')
POLYGON_API_KEY = os.getenv('POLYGON_API_KEY')
POLYGON_PLAN = os.getenv('POLYGON_PLAN', '').strip().lower()

OPENROUTER_BASE_URL = 'https://openrouter.ai/api/v1'
openrouter_client = AsyncOpenAI(base_url=OPENROUTER_BASE_URL, api_key=OPENROUTER_API_KEY) if OPENROUTER_API_KEY else None


def get_model(model_name: str = OPENROUTER_MODEL):
    if openrouter_client:
        return OpenAIChatCompletionsModel(model=model_name, openai_client=openrouter_client)
    return model_name


def market_mcp_params():
    if POLYGON_PLAN in {'paid', 'realtime'} and POLYGON_API_KEY:
        return {
            'command': 'uvx',
            'args': ['--from', 'git+https://github.com/polygon-io/mcp_polygon@v0.1.0', 'mcp_polygon'],
            'env': {'POLYGON_API_KEY': POLYGON_API_KEY},
        }
    return {'command': 'uv', 'args': ['run', str(PROJECT_ROOT / 'market_server.py')]}


def trader_mcp_server_params():
    return [
        {'command': 'uv', 'args': ['run', str(PROJECT_ROOT / 'accounts_server.py')]},
        {'command': 'uv', 'args': ['run', str(PROJECT_ROOT / 'push_server.py')]},
        market_mcp_params(),
    ]


def researcher_mcp_server_params(name: str):
    return [
        {'command': 'uvx', 'args': ['mcp-server-fetch']},
        {
            'command': 'npx',
            'args': ['-y', 'mcp-memory-libsql'],
            'env': {'LIBSQL_URL': f'file:{BASE_DIR / f"{name.lower()}_memory.db"}'},
        },
    ]


@function_tool
def search_serper(query: str) -> str:
    """Search the web using Serper and return a concise text result list."""
    if not SERPER_API_KEY:
        return 'SERPER_API_KEY is not configured.'
    response = requests.post(
        'https://google.serper.dev/search',
        headers={'X-API-KEY': SERPER_API_KEY, 'Content-Type': 'application/json'},
        json={'q': query},
        timeout=30,
    )
    response.raise_for_status()
    data = response.json()
    organic = data.get('organic', [])[:5]
    lines = []
    for item in organic:
        title = item.get('title', 'Untitled')
        link = item.get('link', '')
        snippet = item.get('snippet', '')
        lines.append(f"- {title} | {link} | {snippet}")
    return '\n'.join(lines) if lines else 'No Serper results found.'


class DeskTrader:
    def __init__(self, name: str, strategy: str, model_name: str | None = None):
        self.name = name
        self.strategy = strategy
        self.model_name = model_name or OPENROUTER_MODEL
        self.account = Account.get(name)
        if not self.account.get_strategy().strip():
            self.account.reset(strategy)

    def account_snapshot(self) -> str:
        data = json.loads(self.account.report())
        data.pop('portfolio_value_time_series', None)
        return json.dumps(data)

    async def get_researcher_tool(self, researcher_servers) -> Tool:
        researcher = Agent(
            name=f'{self.name} Researcher',
            instructions=researcher_instructions(),
            model=get_model(self.model_name),
            mcp_servers=researcher_servers,
            tools=[search_serper],
        )
        return researcher.as_tool(
            tool_name='Researcher',
            tool_description=research_tool_description(),
        )

    async def run(self) -> str:
        async with AsyncExitStack() as trader_stack:
            trader_servers = [
                await trader_stack.enter_async_context(MCPServerStdio(params, client_session_timeout_seconds=90))
                for params in trader_mcp_server_params()
            ]
            async with AsyncExitStack() as researcher_stack:
                researcher_servers = [
                    await researcher_stack.enter_async_context(MCPServerStdio(params, client_session_timeout_seconds=90))
                    for params in researcher_mcp_server_params(self.name)
                ]
                researcher_tool = await self.get_researcher_tool(researcher_servers)
                agent = Agent(
                    name=self.name,
                    instructions=trader_instructions(self.name, self.account.get_strategy(), self.account_snapshot()),
                    model=get_model(self.model_name),
                    tools=[researcher_tool],
                    mcp_servers=trader_servers,
                )
                result = await Runner.run(agent, trader_message(), max_turns=20)
        summary = str(result.final_output)
        log_trader_action(self.name, summary)
        return summary


class TradingDesk:
    def __init__(self):
        init_db()
        self.traders = [
            DeskTrader('Warren', waren_strategy),
            DeskTrader('Cathie', cathie_strategy),
        ]

    def reset(self):
        for trader in self.traders:
            trader.account.reset(trader.strategy)

    def portfolio_snapshot(self) -> dict[str, Any]:
        snapshot: dict[str, Any] = {'traders': [], 'desk_holdings': {}, 'cash': 0.0, 'portfolio_value': 0.0}
        for trader in self.traders:
            account = Account.get(trader.name)
            account_json = json.loads(account.report())
            trader_entry = {
                'name': trader.name,
                'balance': account_json['balance'],
                'holdings': account_json['holdings'],
                'portfolio_value': account_json['total_portfolio_value'],
                'strategy': account_json['strategy'],
            }
            snapshot['traders'].append(trader_entry)
            snapshot['cash'] += account_json['balance']
            snapshot['portfolio_value'] += account_json['total_portfolio_value']
            for symbol, qty in account_json['holdings'].items():
                snapshot['desk_holdings'][symbol] = snapshot['desk_holdings'].get(symbol, 0) + qty
        return snapshot

    async def review_with_manager(self, snapshot: dict[str, Any]) -> str:
        agent = Agent(
            name='Portfolio Manager',
            instructions=portfolio_manager_instructions(json.dumps(snapshot, indent=2)),
            model=get_model(),
        )
        result = await Runner.run(agent, 'Review the desk and produce a short portfolio-management summary.')
        summary = str(result.final_output)
        log_desk_review('manager', summary.split('\n')[0][:200], summary)
        return summary

    async def review_with_risk(self, snapshot: dict[str, Any]) -> str:
        agent = Agent(
            name='Risk Officer',
            instructions=risk_officer_instructions(json.dumps(snapshot, indent=2)),
            model=get_model(),
        )
        result = await Runner.run(agent, 'Review the desk for concentration, duplication, cash, and risk posture.')
        summary = str(result.final_output)
        first_line = summary.split('\n')[0][:200]
        log_desk_review('risk', first_line, summary)
        if any(word in summary.lower() for word in ['high risk', 'severe', 'concentration', 'overexposed', 'warning']):
            log_risk_alert('warning', first_line)
        return summary

    async def run_cycle(self) -> dict[str, Any]:
        pre_snapshot = self.portfolio_snapshot()
        manager_pre = await self.review_with_manager(pre_snapshot)
        risk_pre = await self.review_with_risk(pre_snapshot)
        trader_summaries = await self.run_traders()
        post_snapshot = self.portfolio_snapshot()
        manager_post = await self.review_with_manager(post_snapshot)
        risk_post = await self.review_with_risk(post_snapshot)
        return {
            'manager_pre': manager_pre,
            'risk_pre': risk_pre,
            'trader_summaries': trader_summaries,
            'manager_post': manager_post,
            'risk_post': risk_post,
            'snapshot': post_snapshot,
        }

    async def run_traders(self) -> list[dict[str, str]]:
        outputs = await asyncio.gather(*[trader.run() for trader in self.traders])
        return [{'name': trader.name, 'summary': summary} for trader, summary in zip(self.traders, outputs)]

    def snapshot_tables(self):
        snapshot = self.portfolio_snapshot()
        traders_df = pd.DataFrame(snapshot['traders'])
        holdings_df = pd.DataFrame(
            [{'symbol': symbol, 'quantity': qty} for symbol, qty in snapshot['desk_holdings'].items()]
        ) if snapshot['desk_holdings'] else pd.DataFrame(columns=['symbol', 'quantity'])
        actions_df = pd.DataFrame(read_recent_actions(), columns=['cycle_time', 'trader_name', 'summary'])
        reviews_df = pd.DataFrame(read_recent_reviews(), columns=['cycle_time', 'review_type', 'summary', 'details'])
        alerts_df = pd.DataFrame(read_recent_alerts(), columns=['cycle_time', 'severity', 'message'])
        return traders_df, holdings_df, actions_df, reviews_df, alerts_df
