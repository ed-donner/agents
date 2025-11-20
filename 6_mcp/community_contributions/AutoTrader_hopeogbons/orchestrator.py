"""
Orchestrator Agent for managing shared MCP server connections across all traders.

This module provides a resource pooling layer that creates and manages shared MCP
server connections, reducing subprocess overhead from ~32 to ~6-9 per trading cycle.
"""

from contextlib import AsyncExitStack
from typing import List
import asyncio
from traders import Trader
from agents.mcp import MCPServerStdio
from mcp_params import trader_mcp_server_params, researcher_mcp_server_params
from tracers import LogTracer
from agents import add_trace_processor
from market import is_market_open
from dotenv import load_dotenv
import os

load_dotenv(override=True)

RUN_EVERY_N_MINUTES = int(os.getenv("RUN_EVERY_N_MINUTES", "60"))
RUN_EVEN_WHEN_MARKET_IS_CLOSED = (
    os.getenv("RUN_EVEN_WHEN_MARKET_IS_CLOSED", "false").strip().lower() == "true"
)


class OrchestratorAgent:
    """
    Orchestrator that manages shared MCP server connections for all traders.
    
    This reduces the number of spawned subprocesses by sharing trader MCP servers
    (accounts, push, market) across all traders while maintaining separate researcher
    servers for each trader (to keep separate memory databases).
    """
    
    def __init__(self, trader_configs: List[tuple]):
        """
        Initialize orchestrator with trader configurations.
        
        Args:
            trader_configs: List of (name, lastname, model_name) tuples
        """
        self.trader_configs = trader_configs
        self.traders: List[Trader] = []
        self.shared_trader_mcp_servers = []
        self.researcher_mcp_servers_by_name = {}
        self.stack = AsyncExitStack()
        
    async def __aenter__(self):
        """Set up shared MCP servers and create traders."""
        # Create shared trader MCP servers (accounts, push, market)
        # These are shared across ALL traders
        print("Creating shared trader MCP servers...", flush=True)
        self.shared_trader_mcp_servers = [
            await self.stack.enter_async_context(
                MCPServerStdio(params, client_session_timeout_seconds=120)
            )
            for params in trader_mcp_server_params
        ]
        print(f"Created {len(self.shared_trader_mcp_servers)} shared trader MCP servers", flush=True)
        
        # Create separate researcher MCP servers for each trader
        # (They need separate memory databases)
        print("Creating researcher MCP servers for each trader...", flush=True)
        for name, lastname, model_name in self.trader_configs:
            researcher_servers = [
                await self.stack.enter_async_context(
                    MCPServerStdio(params, client_session_timeout_seconds=120)
                )
                for params in researcher_mcp_server_params(name)
            ]
            self.researcher_mcp_servers_by_name[name] = researcher_servers
            print(f"Created {len(researcher_servers)} researcher MCP servers for {name}", flush=True)
        
        # Create trader instances
        self.traders = [
            Trader(name, lastname, model_name)
            for name, lastname, model_name in self.trader_configs
        ]
        print(f"Created {len(self.traders)} traders", flush=True)
        
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Clean up all MCP server connections."""
        await self.stack.aclose()
    
    async def run_trading_cycle(self):
        """
        Execute one trading cycle for all traders with shared resources.
        
        This runs all traders in parallel using asyncio.gather, but they
        all share the same trader MCP server connections.
        """
        # Run all traders in parallel with shared resources
        await asyncio.gather(*[
            trader.run_with_shared_servers(
                self.shared_trader_mcp_servers,
                self.researcher_mcp_servers_by_name[trader.name]
            )
            for trader in self.traders
        ])
    
    async def run_forever(self):
        """
        Main execution loop - runs trading cycles on schedule.
        
        This maintains the same scheduling logic as the original trading_floor.py
        but with shared resource management.
        """
        add_trace_processor(LogTracer())
        print(f"Starting orchestrator - will run every {RUN_EVERY_N_MINUTES} minutes", flush=True)
        
        while True:
            if RUN_EVEN_WHEN_MARKET_IS_CLOSED or is_market_open():
                print("\n" + "="*60, flush=True)
                print("Starting new trading cycle...", flush=True)
                print("="*60, flush=True)
                await self.run_trading_cycle()
                print("Trading cycle completed", flush=True)
            else:
                print("Market is closed, skipping run", flush=True)
            
            await asyncio.sleep(RUN_EVERY_N_MINUTES * 60)


async def run_orchestrator():
    """
    Main entry point for orchestrator-based trading floor.
    
    Creates orchestrator with trader configurations and runs forever.
    """
    from trading_floor import names, lastnames, model_names
    
    trader_configs = list(zip(names, lastnames, model_names))
    
    async with OrchestratorAgent(trader_configs) as orchestrator:
        await orchestrator.run_forever()


if __name__ == "__main__":
    asyncio.run(run_orchestrator())

