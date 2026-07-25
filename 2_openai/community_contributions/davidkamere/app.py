import asyncio
import json

import gradio as gr
from dotenv import load_dotenv

from agents_core import ClarifyingDeepResearcher

load_dotenv(override=True)

researcher = ClarifyingDeepResearcher()


def format_clarification_questions(questions):
    if not questions:
        return ""
    lines = []
    for i, item in enumerate(questions, start=1):
        lines.append(f"{i}. {item.question}  \n   Why: {item.reason}")
    return "\n\n".join(lines)


def format_plan(plan):
    if not plan:
        return ""
    lines = [f"## Objective\n{plan.objective}\n", f"## Report Angle\n{plan.report_angle}\n", "## Search Plan"]
    for item in plan.searches:
        lines.append(f"- **P{item.priority}** `{item.query}`: {item.reason}")
    return "\n".join(lines)


def format_findings(findings):
    if not findings:
        return ""
    blocks = []
    for finding in findings:
        sources = ", ".join(finding.key_sources) if finding.key_sources else "No sources listed"
        blocks.append(
            f"### {finding.query}\n"
            f"{finding.summary}\n\n"
            f"**Key sources:** {sources}"
        )
    return "\n\n".join(blocks)


def format_followups(followups):
    if not followups:
        return ""
    return "\n".join([f"- {item}" for item in followups])


async def analyze_query(query: str):
    if not query.strip():
        return (
            "Please enter a research query.",
            "",
            "",
            gr.update(visible=False),
            gr.update(visible=False),
            gr.update(visible=False),
            "",
            "",
        )

    result = await researcher.analyze_query(query)

    if result["status"] == "blocked":
        guardrail_text = f"Blocked: {result['guardrail'].reason}"
        return (
            guardrail_text,
            "",
            "",
            gr.update(visible=False),
            gr.update(visible=False),
            gr.update(visible=False),
            "",
            "",
        )

    clarification = result["clarification"]
    guardrail_text = f"Allowed: {result['guardrail'].reason}"
    clarification_summary = json.dumps(clarification.model_dump(), indent=2)

    if clarification.needs_clarification:
        questions_md = format_clarification_questions(clarification.questions)
        return (
            guardrail_text,
            clarification_summary,
            questions_md,
            gr.update(visible=True),
            gr.update(visible=True),
            gr.update(visible=False),
            "",
            "",
        )

    assumptions_text = "\n".join(f"- {item}" for item in clarification.assumptions) if clarification.assumptions else "No assumptions provided."
    return (
        guardrail_text,
        clarification_summary,
        assumptions_text,
        gr.update(visible=True, value=assumptions_text),
        gr.update(visible=True),
        gr.update(visible=False),
        "",
        "",
    )


async def run_research(query: str, clarification_answers: str):
    if not query.strip():
        return "", "", "", "Please enter a research query.", "", ""

    result = await researcher.run_full_research(query, clarification_answers)

    if result["status"] == "blocked":
        return "", "", "", f"Blocked: {result['guardrail'].reason}", "", ""

    plan_md = format_plan(result["plan"])
    findings_md = format_findings(result["findings"])
    report_md = result["report"].markdown_report
    followups_md = format_followups(result["report"].follow_up_questions)
    saved_path = result.get("saved_report", {}).get("path", "")
    saved_report_md = f"Saved to: `{saved_path}`" if saved_path else ""
    return plan_md, findings_md, report_md, result["report"].executive_summary, followups_md, saved_report_md


with gr.Blocks(theme=gr.themes.Default(primary_hue="blue")) as ui:
    gr.Markdown("# Deep Researcher")
    gr.Markdown(
        "A multi-agent research assistant with guardrails, clarifying questions, structured outputs, "
        "web research, and report generation."
    )

    with gr.Row():
        query = gr.Textbox(
            label="Research Query",
            placeholder="Example: Compare the latest AI agent frameworks for internal enterprise tooling.",
            lines=3,
        )

    analyze_button = gr.Button("1. Analyze Query", variant="primary")

    guardrail_status = gr.Markdown(label="Guardrail Status")
    clarification_json = gr.Code(label="Clarification Decision", language="json")
    clarification_questions = gr.Markdown(label="Clarifying Questions / Assumptions")

    clarification_answers = gr.Textbox(
        label="Clarification Answers",
        placeholder="Answer the clarifying questions here, or accept the assumptions and refine them if needed.",
        lines=6,
        visible=False,
    )

    run_button = gr.Button("2. Run Research", visible=False)

    with gr.Row():
        executive_summary = gr.Markdown(label="Executive Summary")
        followup_questions = gr.Markdown(label="Follow-up Questions")

    saved_report = gr.Markdown(label="Saved Report")
    research_plan = gr.Markdown(label="Research Plan")
    findings = gr.Markdown(label="Findings")
    final_report = gr.Markdown(label="Final Report")

    analyze_button.click(
        fn=analyze_query,
        inputs=[query],
        outputs=[
            guardrail_status,
            clarification_json,
            clarification_questions,
            clarification_answers,
            run_button,
            final_report,
            research_plan,
            findings,
        ],
    )

    run_button.click(
        fn=run_research,
        inputs=[query, clarification_answers],
        outputs=[
            research_plan,
            findings,
            final_report,
            executive_summary,
            followup_questions,
            saved_report,
        ],
    )

ui.launch()
