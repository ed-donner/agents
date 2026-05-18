import gradio as gr
import asyncio
import json
from security_agents import run_pipeline


CSS = """
@import url('https://fonts.googleapis.com/css2?family=Share+Tech+Mono&family=Rajdhani:wght@400;600;700&display=swap');

body, .gradio-container {
    background: #080c10 !important;
    color: #c8d8e8 !important;
    font-family: 'Rajdhani', sans-serif !important;
}

/* Header */
.inc-header {
    border-bottom: 1px solid #1a3a2a;
    padding: 18px 0 10px 0;
    text-align: center;
}
.inc-title {
    font-size: 2rem;
    font-weight: 700;
    letter-spacing: 0.12em;
    color: #00ff88;
    text-shadow: 0 0 18px #00ff8866;
    font-family: 'Share Tech Mono', monospace;
}
.inc-sub {
    font-size: 0.85rem;
    color: #4a8a6a;
    letter-spacing: 0.2em;
    margin-top: 4px;
}

/* Panels */
.panel-label {
    font-family: 'Share Tech Mono', monospace;
    font-size: 0.78rem;
    letter-spacing: 0.18em;
    color: #00cc66;
    border-left: 3px solid #00cc66;
    padding-left: 8px;
    margin-bottom: 6px;
}
.panel-label.inv  { color: #00aaff; border-color: #00aaff; }
.panel-label.resp { color: #ff9900; border-color: #ff9900; }

/* Terminal boxes */
.terminal-box {
    background: #0b1118 !important;
    border: 1px solid #1a2a3a !important;
    border-radius: 6px !important;
    font-family: 'Share Tech Mono', monospace !important;
    font-size: 0.82rem !important;
    color: #a8d8b8 !important;
    padding: 14px !important;
    min-height: 180px;
}
.terminal-box textarea {
    background: transparent !important;
    color: inherit !important;
    font-family: inherit !important;
    font-size: inherit !important;
    border: none !important;
    outline: none !important;
    resize: vertical;
}

/* Status badge */
.sev-CRITICAL { color: #ff3333 !important; font-weight: 700; }
.sev-HIGH     { color: #ff7700 !important; font-weight: 700; }
.sev-MEDIUM   { color: #ffcc00 !important; font-weight: 600; }
.sev-LOW      { color: #00dd88 !important; }

/* Run button */
.run-btn {
    background: linear-gradient(135deg, #003322, #005544) !important;
    border: 1px solid #00cc66 !important;
    color: #00ff88 !important;
    font-family: 'Share Tech Mono', monospace !important;
    font-size: 1rem !important;
    letter-spacing: 0.15em !important;
    border-radius: 4px !important;
    box-shadow: 0 0 12px #00cc6633 !important;
    transition: box-shadow 0.2s !important;
}
.run-btn:hover {
    box-shadow: 0 0 28px #00cc6688 !important;
}

footer { display: none !important; }
"""

JS_DARK = """
function refresh() {
    const url = new URL(window.location);
    if (url.searchParams.get('__theme') !== 'dark') {
        url.searchParams.set('__theme', 'dark');
        window.location.href = url.href;
    }
}
"""

SAMPLE_LOGS = """\
2026-03-26 02:11:01 WARN  sshd: Failed password for root from 185.220.101.45 port 54321
2026-03-26 02:11:03 WARN  sshd: Failed password for admin from 185.220.101.45 port 54322
2026-03-26 02:11:05 WARN  sshd: Failed password for ubuntu from 185.220.101.45 port 54323
2026-03-26 02:11:07 WARN  sshd: Failed password for deploy from 185.220.101.45 port 54324
2026-03-26 02:11:09 WARN  sshd: Failed password for pi from 185.220.101.45 port 54325
2026-03-26 02:11:11 WARN  sshd: Failed password for test from 185.220.101.45 port 54326
2026-03-26 02:11:30 INFO  sshd: Accepted publickey for alice from 10.0.1.5
2026-03-26 02:12:00 WARN  sshd: Failed password for root from 91.241.19.223 port 60001
2026-03-26 02:12:05 WARN  sshd: Failed password for root from 91.241.19.223 port 60002
2026-03-26 02:12:09 WARN  sshd: Failed password for root from 91.241.19.223 port 60003
2026-03-26 02:12:12 WARN  sshd: Failed password for root from 91.241.19.223 port 60004
2026-03-26 03:00:01 WARN  firewall: port scan detected from 185.220.101.45
2026-03-26 03:05:00 ERROR sudo: www-data ran /bin/bash as root — FAILED
"""


def _fmt_detector(d: dict) -> str:
    if "raw" in d:
        return d["raw"]
    lines = [f"[ SUMMARY ] {d.get('summary', 'N/A')}\n"]
    for a in d.get("anomalies", []):
        sev = a.get("severity", "?")
        lines.append(f"{'━'*52}")
        lines.append(f"  TYPE     : {a.get('type', '?').upper()}")
        lines.append(f"  SEVERITY : {sev}")
        lines.append(f"  SRC IP   : {a.get('src_ip') or 'N/A'}")
        lines.append(f"  USER     : {a.get('user') or 'N/A'}")
        lines.append(f"  COUNT    : {a.get('event_count', '?')}")
        lines.append(f"  WINDOW   : {a.get('time_window', 'N/A')}")
    return "\n".join(lines)


def _fmt_investigator(d: dict) -> str:
    if "raw" in d:
        return d["raw"]
    lines = [
        f"[ {d.get('incident_title', 'INCIDENT REPORT')} ]",
        f"  Severity   : {d.get('severity', '?')}",
        f"  Confidence : {d.get('confidence', '?')}",
        "",
        "WHAT HAPPENED:",
        f"  {d.get('what_happened', 'N/A')}",
        "",
        "TIMELINE:",
        f"  {d.get('timeline', 'N/A')}",
        "",
        "THREAT ACTORS:",
    ]
    for ta in d.get("threat_actors", []):
        lines.append(f"  ▸ {ta.get('ip')} — {ta.get('reputation')} — {ta.get('role')}")
    return "\n".join(lines)


def _fmt_responder(d: dict) -> str:
    if "raw" in d:
        return d["raw"]
    lines = []

    def _section(title, items):
        if items:
            lines.append(f"\n[ {title} ]")
            for item in items:
                lines.append(f"  ▸ {item}")

    _section("IMMEDIATE ACTIONS", d.get("immediate_actions", []))
    _section("SHORT-TERM ACTIONS", d.get("short_term_actions", []))
    _section("LONG-TERM HARDENING", d.get("long_term_hardening", []))

    if d.get("block_list"):
        lines.append("\n[ BLOCK LIST ]")
        for ip in d["block_list"]:
            lines.append(f"  iptables -I INPUT -s {ip} -j DROP")

    escalate = d.get("escalate_to_human", False)
    lines.append(f"\n[ ESCALATE TO HUMAN ] {'⚠ YES — ' + str(d.get('escalation_reason','')) if escalate else 'No'}")
    return "\n".join(lines)


def _severity_html(result: dict) -> str:
    sev = result.get("investigator", {}).get("severity", "UNKNOWN")
    color = {"CRITICAL": "#ff3333", "HIGH": "#ff7700", "MEDIUM": "#ffcc00", "LOW": "#00dd88"}.get(sev, "#888")
    return (
        f'<div style="font-family:Share Tech Mono,monospace;font-size:1.1rem;'
        f'color:{color};text-shadow:0 0 10px {color}55;padding:6px 0">'
        f'[ SEVERITY: {sev} ]</div>'
    )



async def _investigate(log_text: str):
    logs = log_text.strip() if log_text.strip() else None
    result = await run_pipeline(logs)
    return (
        _fmt_detector(result["detector"]),
        _fmt_investigator(result["investigator"]),
        _fmt_responder(result["responder"]),
        _severity_html(result),
        json.dumps(result, indent=2),
    )


def investigate(log_text: str):
    return asyncio.run(_investigate(log_text))


with gr.Blocks(css=CSS, js=JS_DARK, title="Incident Investigator") as demo:

    gr.HTML("""
    <div class="inc-header">
      <div class="inc-title">⬡ AUTONOMOUS INCIDENT INVESTIGATOR</div>
      <div class="inc-sub">DETECTOR · INVESTIGATOR · RESPONDER</div>
    </div>
    """)

    with gr.Row():
        with gr.Column(scale=1):
            gr.HTML('<div class="panel-label">▸ INPUT LOGS</div>')
            log_input = gr.Textbox(
                label="",
                placeholder="Paste logs here — or leave blank to use simulated server logs",
                lines=14,
                value=SAMPLE_LOGS,
                elem_classes=["terminal-box"],
            )
            run_btn = gr.Button("⬡  RUN INVESTIGATION", elem_classes=["run-btn"])
            severity_badge = gr.HTML("<div></div>")

    with gr.Row():
        with gr.Column():
            gr.HTML('<div class="panel-label">▸ DETECTOR OUTPUT</div>')
            detector_out = gr.Textbox(label="", lines=12, interactive=False, elem_classes=["terminal-box"])

        with gr.Column():
            gr.HTML('<div class="panel-label inv">▸ INVESTIGATOR REPORT</div>')
            investigator_out = gr.Textbox(label="", lines=12, interactive=False, elem_classes=["terminal-box"])

    with gr.Row():
        with gr.Column():
            gr.HTML('<div class="panel-label resp">▸ RESPONDER — ACTION PLAN</div>')
            responder_out = gr.Textbox(label="", lines=10, interactive=False, elem_classes=["terminal-box"])

        with gr.Column():
            gr.HTML('<div class="panel-label" style="color:#555;border-color:#555">▸ RAW JSON OUTPUT</div>')
            raw_out = gr.Code(label="", language="json", lines=10, interactive=False)

    run_btn.click(
        fn=investigate,
        inputs=[log_input],
        outputs=[detector_out, investigator_out, responder_out, severity_badge, raw_out],
    )

if __name__ == "__main__":
    demo.launch()
