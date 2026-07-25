"""MCP server: exposes `crm_*` tools backed by `store.py`."""

import json

from mcp.server.fastmcp import FastMCP

import store

mcp = FastMCP("agentcrm_store")


@mcp.tool()
async def crm_upsert_deal(
    rep_name: str,
    account_name: str,
    stage: str = "discovery",
    value_dollars: float | None = None,
    notes: str | None = None,
) -> str:
    """Create or update a deal for this rep and account. Stages examples: discovery, qualified, proposal, negotiation, closed_won, closed_lost."""
    did = store.upsert_deal(rep_name, account_name, stage, value_dollars, notes)
    return f"Deal id={did} for {account_name} ({rep_name})"


@mcp.tool()
async def crm_link_gmail_thread(deal_id: int, gmail_thread_id: str) -> str:
    """Attach a Gmail thread id to a deal so get_deal_by_thread can resolve context."""
    return store.link_gmail_thread(deal_id, gmail_thread_id)


@mcp.tool()
async def crm_add_touchpoint(
    deal_id: int,
    kind: str,
    summary: str,
    source_ref: str | None = None,
) -> str:
    """Record a touchpoint: kind is one of email, meeting, call, note. source_ref optional (message id, event id)."""
    tid = store.add_touchpoint(deal_id, kind, summary, source_ref)
    return f"Touchpoint id={tid} added to deal {deal_id}"


@mcp.tool()
async def crm_get_deal_by_thread(rep_name: str, gmail_thread_id: str) -> str:
    """Load deal + touchpoints when you know rep and Gmail thread id."""
    d = store.get_deal_by_thread(rep_name, gmail_thread_id)
    return store.deal_bundle_to_json(d) if d else "{}"


@mcp.tool()
async def crm_get_deal_context(deal_id: int) -> str:
    """Full JSON for a deal including recent touchpoints."""
    d = store.get_deal_context(deal_id)
    return store.deal_bundle_to_json(d) if d else "{}"


@mcp.tool()
async def crm_list_active_deals(rep_name: str, limit: int = 20) -> str:
    """List recent deals for a rep with touchpoints (capped)."""
    deals = store.list_active_deals(rep_name, limit)
    return json.dumps(deals, indent=2, default=str)


@mcp.tool()
async def crm_update_stage(deal_id: int, stage: str) -> str:
    """Update pipeline stage."""
    return store.update_deal_stage(deal_id, stage)


@mcp.tool()
async def crm_find_deal_by_account(rep_name: str, account_name: str) -> str:
    """Find a deal by account name for this rep."""
    d = store.find_deal_by_account(rep_name, account_name)
    return store.deal_bundle_to_json(d) if d else "{}"


if __name__ == "__main__":
    mcp.run(transport="stdio")
