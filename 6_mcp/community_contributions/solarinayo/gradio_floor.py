"""
Gradio UI for the Week 6 paper routing floor (VenueScout → AutoTraderClerk).

From repo root:
  uv run python 6_mcp/community_contributions/solarinayo/gradio_floor.py
"""

from __future__ import annotations

import gradio as gr

from run_floor import run_floor


def _parse_symbols(s: str) -> list[str]:
    out: list[str] = []
    for chunk in (s or "").replace(",", " ").split():
        t = chunk.strip().upper()
        if t:
            out.append(t)
    return out


async def run_clicked(goal: str, symbols_csv: str, risk: str) -> tuple[str, str]:
    goal = (goal or "").strip()
    if not goal:
        return "### VenueScout\n\n_Add a goal above._", "### AutoTraderClerk\n\n_Waiting._"
    syms = _parse_symbols(symbols_csv)
    if not syms:
        return (
            "### VenueScout\n\n_Add at least one symbol (comma-separated)._",
            "### AutoTraderClerk\n\n_Waiting._",
        )
    profile = (risk or "balanced").strip().lower()
    scout, clerk = await run_floor(goal, syms, profile)
    return f"### VenueScout\n\n{scout}", f"### AutoTraderClerk\n\n{clerk}"


with gr.Blocks(title="Week 6 — paper multi-exchange floor") as demo:
    gr.Markdown(
        "### Multi-agent paper floor (MCP)\n"
        "**VenueScout** (routing tools) → **AutoTraderClerk** (paper journal). "
        "Paper simulation only — **not financial advice**."
    )
    goal = gr.Textbox(
        label="Goal",
        lines=3,
        placeholder="e.g. Compare routing for a small diversification check (paper only).",
    )
    symbols = gr.Textbox(
        label="Symbols (comma or space separated)",
        value="BTC, AAPL",
    )
    risk = gr.Dropdown(
        label="Risk profile",
        choices=["conservative", "moderate", "balanced", "aggressive"],
        value="moderate",
    )
    go = gr.Button("Run floor", variant="primary")
    gr.Markdown("#### VenueScout")
    scout_md = gr.Markdown()
    gr.Markdown("#### AutoTraderClerk")
    clerk_md = gr.Markdown()
    go.click(run_clicked, [goal, symbols, risk], [scout_md, clerk_md])

if __name__ == "__main__":
    demo.launch(inbrowser=True)
