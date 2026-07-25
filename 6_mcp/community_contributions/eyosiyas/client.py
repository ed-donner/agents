"""
Entry point: Gradio UI that talks to the FastMCP server over stdio (subprocess).

Uses the official `mcp` client. The server (`main.py`) uses `FastMCP` from
`mcp.server` (bundled with the `mcp` package), not the separate PyPI `fastmcp`.
"""
from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

import gradio as gr
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.types import CallToolResult, TextContent

_DIR = Path(__file__).resolve().parent
_MAIN = _DIR / "main.py"


def _parse_tool_result(result: CallToolResult) -> dict:
    if result.isError:
        msg = ""
        for block in result.content:
            if isinstance(block, TextContent):
                msg += block.text
        raise RuntimeError(msg or "Tool returned an error")
    if result.structuredContent:
        data = dict(result.structuredContent)
        inner = data.get("result")
        if isinstance(inner, dict) and set(data.keys()) <= {"result"}:
            return inner
        return data
    for block in result.content:
        if isinstance(block, TextContent):
            try:
                return json.loads(block.text)
            except json.JSONDecodeError:
                return {"_raw": block.text}
    return {}


def _fmt_analysis_md(analysis: dict) -> str:
    summary = (analysis.get("summary") or "").strip() or "_No summary returned._"
    steps = analysis.get("structured_steps") or []
    if steps:
        lines = "\n".join(f"{i + 1}. {s}" for i, s in enumerate(steps))
        steps_block = lines
    else:
        steps_block = "_No structured steps._"
    return f"""### Summary

{summary}

### Structured process steps

{steps_block}
"""


def _fmt_gaps_md(gaps: dict) -> str:
    items = gaps.get("gaps") or []
    if not items:
        return "_No gaps detected — your process covers the suggested standard steps._"
    lines = []
    for i, g in enumerate(items, 1):
        step = g.get("step", "?")
        pri = g.get("priority", "?")
        lines.append(f"{i}. **{step}**  \n   Priority: **{pri}**")
    return "### Detected gaps\n\n" + "\n\n".join(lines)


def _fmt_recommendations_md(rec: dict) -> str:
    items = rec.get("recommendations") or []
    if not items:
        return "_No recommendations._"
    parts = []
    for i, r in enumerate(items, 1):
        action = r.get("action", "")
        reason = r.get("reason", "")
        impact = r.get("impact", "")
        parts.append(
            f"{i}. **{action}**\n\n   - *Why:* {reason}\n   - *Impact:* {impact}"
        )
    return "### Recommendations\n\n" + "\n\n".join(parts)


def _fmt_redesigned_md(improved: dict) -> str:
    steps = improved.get("improved_process") or []
    if not steps:
        return "_No redesigned process returned._"
    lines = "\n".join(f"{i + 1}. {s}" for i, s in enumerate(steps))
    return "### Proposed workflow\n\n" + lines


def _fmt_full_report_plain(
    analysis: dict, gaps: dict, recommendations: dict, improved: dict
) -> str:
    """Plain text for the copy-friendly panel (no markdown)."""
    parts: list[str] = []
    parts.append("ANALYSIS")
    parts.append("=" * 44)
    parts.append((analysis.get("summary") or "").strip() or "(no summary)")
    parts.append("")
    steps = analysis.get("structured_steps") or []
    if steps:
        parts.append("Structured steps:")
        for i, s in enumerate(steps, 1):
            parts.append(f"  {i}. {s}")
    parts.append("")
    parts.append("GAPS")
    parts.append("=" * 44)
    gitems = gaps.get("gaps") or []
    if not gitems:
        parts.append("(none)")
    else:
        for i, g in enumerate(gitems, 1):
            parts.append(
                f"  {i}. {g.get('step', '?')} [priority: {g.get('priority', '?')}]"
            )
    parts.append("")
    parts.append("RECOMMENDATIONS")
    parts.append("=" * 44)
    ritems = recommendations.get("recommendations") or []
    if not ritems:
        parts.append("(none)")
    else:
        for i, r in enumerate(ritems, 1):
            parts.append(f"  {i}. {r.get('action', '')}")
            parts.append(f"     Why: {r.get('reason', '')}")
            parts.append(f"     Impact: {r.get('impact', '')}")
    parts.append("")
    parts.append("REDESIGNED PROCESS")
    parts.append("=" * 44)
    imp = improved.get("improved_process") or []
    if not imp:
        parts.append("(none)")
    else:
        for i, s in enumerate(imp, 1):
            parts.append(f"  {i}. {s}")
    return "\n".join(parts)


async def _run_process_audit(
    domain: str, process_name: str, steps_text: str
) -> tuple[str, str, str, str, str]:
    process_steps = [s.strip() for s in steps_text.split("\n") if s.strip()]
    if not process_steps:
        raise ValueError("Add at least one process step (non-empty line).")

    params = StdioServerParameters(
        command=sys.executable,
        args=[str(_MAIN)],
        cwd=str(_DIR),
    )

    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            async def call(name: str, arguments: dict) -> dict:
                raw = await session.call_tool(name, arguments=arguments)
                return _parse_tool_result(raw)

            analysis = await call(
                "tool_analyze_process",
                {"input": {"process_steps": process_steps}},
            )
            detect_input = {
                "domain": domain,
                "process_name": process_name,
                "process_steps": process_steps,
            }
            gaps = await call("tool_detect_gaps", {"input": detect_input})
            recommendations = await call(
                "tool_generate_recommendations",
                {"input": {"gaps": gaps.get("gaps", [])}},
            )
            improved = await call(
                "tool_redesign_process",
                {
                    "input": {
                        "original_steps": process_steps,
                        "recommendations": recommendations.get("recommendations", []),
                    }
                },
            )

    return (
        _fmt_analysis_md(analysis),
        _fmt_gaps_md(gaps),
        _fmt_recommendations_md(recommendations),
        _fmt_redesigned_md(improved),
        _fmt_full_report_plain(analysis, gaps, recommendations, improved),
    )


def run_process_audit(domain, process_name, steps_text):
    try:
        return asyncio.run(_run_process_audit(domain, process_name, steps_text))
    except Exception as e:
        raise gr.Error(str(e)) from e


# --- UI ---------------------------------------------------------------------------

_THEME = gr.themes.Soft(
    primary_hue="slate",
    secondary_hue="blue",
    neutral_hue="slate",
    font=[gr.themes.GoogleFont("Source Sans 3"), "ui-sans-serif", "system-ui", "sans-serif"],
)

_CUSTOM_CSS = """
.results-markdown { max-height: 420px; overflow-y: auto; padding: 0.75rem 1rem; }
.results-markdown h3 { margin-top: 0.5rem; margin-bottom: 0.5rem; font-size: 1.05rem; }
.gradio-container { max-width: 1100px !important; margin: auto !important; }
footer { visibility: hidden; }
"""

with gr.Blocks(
    theme=_THEME,
    css=_CUSTOM_CSS,
    title="Consultant AI — Process audit",
) as demo:
    gr.Markdown(
        """
# Consultant AI — process audit

Describe a workflow, set the **domain** and **process name**, then run the audit.  
Results are organized in **tabs**; use **Complete report** for a single scrollable view suitable for copying.
        """
    )

    with gr.Row():
        with gr.Column(scale=1):
            gr.Markdown("### Inputs")
            domain_input = gr.Textbox(
                label="Domain",
                placeholder="e.g. Recruitment, Finance, Customer support",
                lines=1,
            )
            process_input = gr.Textbox(
                label="Process name",
                placeholder="e.g. New hire onboarding",
                lines=1,
            )
            steps_input = gr.Textbox(
                label="Process steps (one per line)",
                lines=10,
                max_lines=24,
                placeholder="CV screening\nPhone screen\nTechnical interview\nOffer",
            )
            run_btn = gr.Button("Run process audit", variant="primary", size="lg")

        with gr.Column(scale=2):
            gr.Markdown("### Results")
            with gr.Tabs():
                with gr.Tab("Analysis"):
                    out_analysis = gr.Markdown(
                        value="_Run an audit to see the summary and structured steps._",
                        elem_classes=["results-markdown"],
                    )
                with gr.Tab("Gaps"):
                    out_gaps = gr.Markdown(
                        value="_Gap analysis appears here._",
                        elem_classes=["results-markdown"],
                    )
                with gr.Tab("Recommendations"):
                    out_recs = gr.Markdown(
                        value="_Recommendations appear here._",
                        elem_classes=["results-markdown"],
                    )
                with gr.Tab("Redesigned process"):
                    out_redesign = gr.Markdown(
                        value="_Improved workflow appears here._",
                        elem_classes=["results-markdown"],
                    )
                with gr.Tab("Complete report"):
                    out_full = gr.Textbox(
                        label="Full audit (plain text — copy button below)",
                        lines=22,
                        max_lines=40,
                        show_copy_button=True,
                    )

    run_btn.click(
        fn=run_process_audit,
        inputs=[domain_input, process_input, steps_input],
        outputs=[out_analysis, out_gaps, out_recs, out_redesign, out_full],
        show_progress="full",
    )

if __name__ == "__main__":
    demo.launch()
