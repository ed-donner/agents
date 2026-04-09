from dotenv import load_dotenv

load_dotenv(override=True)

import gradio as gr
from agent import run_traffic_check
from models import TrafficReport, CongestionLevel

CONGESTION_COLORS = {
    CongestionLevel.FREE_FLOW: "#4ade80",
    CongestionLevel.LIGHT: "#a3e635",
    CongestionLevel.MODERATE: "#fbbf24",
    CongestionLevel.HEAVY: "#f97316",
}

CONGESTION_LABELS = {
    CongestionLevel.FREE_FLOW: "Free Flow",
    CongestionLevel.LIGHT: "Light",
    CongestionLevel.MODERATE: "Moderate",
    CongestionLevel.HEAVY: "Heavy",
}

CUSTOM_CSS = """
.gradio-container {
    background-color: #0f172a !important;
}
.main-title {
    color: #f8fafc !important;
    text-align: center;
    margin-bottom: 0 !important;
}
.subtitle {
    color: #94a3b8 !important;
    text-align: center;
    font-size: 16px;
    margin-top: 4px !important;
}
.traffic-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 16px;
    padding: 8px 0;
}
.traffic-card {
    background: #1e293b;
    border-radius: 12px;
    padding: 20px;
    border-left: 4px solid #64748b;
    color: #f8fafc;
}
.traffic-card h3 {
    margin: 0 0 12px 0;
    font-size: 16px;
    color: #f8fafc;
}
.card-field {
    margin: 6px 0;
    font-size: 14px;
    color: #e2e8f0;
}
.card-label {
    color: #94a3b8;
    font-weight: 600;
    margin-right: 6px;
}
.congestion-badge {
    display: inline-block;
    padding: 2px 10px;
    border-radius: 9999px;
    font-size: 12px;
    font-weight: 600;
    color: #0f172a;
}
.incident-item {
    background: #1e293b;
    border: 1px solid #334155;
    border-radius: 8px;
    padding: 12px 16px;
    margin-bottom: 8px;
    color: #e2e8f0;
    font-size: 14px;
}
.incident-severity {
    font-weight: 600;
    margin-right: 8px;
}
.placeholder-text {
    color: #64748b;
    text-align: center;
    padding: 40px 20px;
    font-size: 15px;
}
.timestamp-text {
    color: #64748b !important;
    text-align: center;
    font-size: 13px;
}
"""

PLACEHOLDER_HTML = '<p class="placeholder-text">Click <strong>Run Traffic Check</strong> to fetch live conditions for 6 Kigali roads.</p>'


def render_traffic_cards(report: TrafficReport) -> str:
    cards = ""
    for seg in report.segments:
        color = CONGESTION_COLORS.get(seg.congestion_level, "#64748b")
        label = CONGESTION_LABELS.get(seg.congestion_level, "Unknown")

        delay_text = f"+{seg.delay_minutes} min" if seg.delay_seconds > 0 else "No delay"

        cards += f"""<div class="traffic-card" style="border-left-color: {color};">
<h3>{seg.segment_name}</h3>
<p class="card-field"><span class="card-label">Travel time:</span>{seg.live_travel_time_secs}s (baseline: {seg.base_travel_time_secs}s)</p>
<p class="card-field"><span class="card-label">Status:</span><span class="congestion-badge" style="background: {color};">{label}</span></p>
<p class="card-field"><span class="card-label">Delay:</span>{delay_text}</p>
<p class="card-field"><span class="card-label">Ratio:</span>{seg.congestion_ratio}x</p>
</div>"""

    return f'<div class="traffic-grid">{cards}</div>'


def render_incidents(incidents: list) -> str:
    if not incidents:
        return '<p class="placeholder-text">No active incidents reported.</p>'

    items = ""
    severity_colors = {"Minor": "#fbbf24", "Moderate": "#f97316", "Major": "#ef4444", "Unknown": "#64748b"}
    for inc in incidents:
        sev_color = severity_colors.get(inc.severity, "#64748b")
        delay_text = f" ({inc.delay_seconds}s delay)" if inc.delay_seconds > 0 else ""
        road_text = f" on {inc.road}" if inc.road else ""
        items += f"""<div class="incident-item">
<span class="incident-severity" style="color: {sev_color};">{inc.severity}</span>
{inc.description}{road_text}{delay_text}
</div>"""

    return items


async def check_traffic():
    report = await run_traffic_check()
    cards_html = render_traffic_cards(report)
    incidents_html = render_incidents(report.incidents)
    summary_md = f"### Traffic Summary\n\n{report.summary}"
    timestamp = f"Last checked: {report.checked_at}"
    return summary_md, cards_html, incidents_html, timestamp


with gr.Blocks(
    title="Kigali Traffic Monitor",
    theme=gr.themes.Default(primary_hue="slate"),
    css=CUSTOM_CSS,
) as app:
    gr.Markdown("# Kigali Traffic Monitor", elem_classes="main-title")
    gr.Markdown("Live road conditions for 6 major Kigali corridors", elem_classes="subtitle")

    check_btn = gr.Button("Run Traffic Check", variant="primary")

    summary_display = gr.Markdown(value="Click **Run Traffic Check** to fetch live conditions.")
    cards_display = gr.HTML(value=PLACEHOLDER_HTML)

    gr.Markdown("### Incidents", elem_classes="main-title")
    incidents_display = gr.HTML(value='<p class="placeholder-text">No data yet.</p>')

    timestamp_display = gr.Markdown(value="", elem_classes="timestamp-text")

    check_btn.click(
        fn=check_traffic,
        inputs=[],
        outputs=[summary_display, cards_display, incidents_display, timestamp_display],
    )

if __name__ == "__main__":
    app.launch(inbrowser=True)
