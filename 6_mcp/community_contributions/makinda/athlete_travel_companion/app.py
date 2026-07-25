"""
Gradio UI for Athlete Travel Companion: multi-agent MCP pipeline + destination map (Plotly).

"""

from __future__ import annotations

from dotenv import load_dotenv

load_dotenv(override=True)

import plotly.graph_objects as go

from map_utils import build_destination_map
from pipeline import run_pipeline


async def run_all(situation: str, destination_city: str, country_code: str):
    """Stream status text, then show map, then final agent output."""
    situation = (situation or "").strip()
    dest = (destination_city or "").strip()
    cc = (country_code or "").strip()

    yield (
        "**Working…** Building map (if destination is set), then running the four agents "
        "(Planner → Connector → Health → Log) with MCP tools…",
        _placeholder_figure(),
    )

    fig: go.Figure
    map_note = ""
    if dest:
        fig, map_note = await build_destination_map(dest, cc)
    else:
        fig = _empty_map_prompt()
        map_note = "_No destination city — map skipped._"

    yield (
        f"**Running agent pipeline…**\n\n{map_note}\n",
        fig,
    )

    if not situation:
        situation = (
            "I'm traveling for training. Help me adjust today's session and find venues."
        )

    try:
        report = await run_pipeline(situation)
    except Exception as exc:  # noqa: BLE001
        report = f"**Error:** `{exc}`"

    yield report, fig


def _placeholder_figure() -> go.Figure:
    fig = go.Figure()
    fig.update_layout(
        title="Loading map…",
        height=440,
        annotations=[
            dict(
                text="Please wait",
                xref="paper",
                yref="paper",
                x=0.5,
                y=0.5,
                showarrow=False,
            )
        ],
    )
    return fig


def _empty_map_prompt() -> go.Figure:
    fig = go.Figure()
    fig.update_layout(
        title="Map",
        height=440,
        annotations=[
            dict(
                text="Enter a destination city below to load OpenStreetMap + optional Places pins.",
                xref="paper",
                yref="paper",
                x=0.5,
                y=0.5,
                showarrow=False,
                font=dict(size=13),
            )
        ],
    )
    return fig


def main() -> None:
    import gradio as gr

    with gr.Blocks(title="Athlete Travel Companion") as demo:
        gr.Markdown(
            "## Athlete Travel Companion\n"
            "Describe your trip, fatigue, and goals. **Destination city** drives the "
            "map (geocode + Google Places when configured). Agents use the MCP server "
            "for weather, calendar, logs, gyms, and Telegram."
        )
        situation = gr.Textbox(
            label="Situation & request",
            lines=6,
            placeholder="e.g. 3 days in Boulder from sea level, tight left calf, need a track and easy tempo today…",
        )
        with gr.Row():
            destination_city = gr.Textbox(
                label="Destination city (for map)",
                placeholder="e.g. Boulder",
                scale=2,
            )
            country_code = gr.Textbox(
                label="Country (optional ISO)",
                placeholder="US",
                max_lines=1,
                scale=1,
            )
        run_btn = gr.Button("Run planner & agents", variant="primary")
        report_out = gr.Markdown(label="Agent report")
        map_plot = gr.Plot(label="Map", format="plotly")

        run_btn.click(
            fn=run_all,
            inputs=[situation, destination_city, country_code],
            outputs=[report_out, map_plot],
            show_progress="full",
        )

    demo.queue()
    demo.launch()


if __name__ == "__main__":
    main()
