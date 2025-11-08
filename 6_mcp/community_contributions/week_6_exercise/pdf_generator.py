import os
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch

from agents import Agent, Tool
from config import client, MODEL, PDF_MAX_TOKENS


async def pdf_summary_step(query, research, risk, finance):
    try:
        prompt = f"""
You are the Report Composition Agent.

You have the following inputs:- Clarified Query: {query},  Research Summary: {research}, Risk Summary: {risk}, Finance Summary: {finance}

Task:Write a concise, professional report synthesizing these sections. Include:1. Executive Summary2. Key Findings3. Recommendations4. Conclusion. Use clear headings, business tone, and coherent transitions.
"""
        completion = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": "You are a precise report writer."},
                {"role": "user", "content": prompt},
            ],
            max_tokens=PDF_MAX_TOKENS,
            temperature=0.3,
        )
        report_text = completion.choices[0].message.content.strip()
    except Exception as e:
        print(f"[pdf_generator] API error: {e}")
        report_text = (
            "APi."
        )

    return report_text


def build_pdf(report_text: str, filename: str = None) -> str:
    if not filename:
        filename = f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    filepath = os.path.abspath(filename)
    doc = SimpleDocTemplate(filepath, pagesize=A4)
    styles = getSampleStyleSheet()
    story = []
    story.append(Paragraph("<b>Automated Analysis Report</b>", styles["Title"]))
    story.append(Spacer(1, 0.2 * inch))
    story.append(Paragraph(datetime.now().strftime("%B %d, %Y %H:%M"), styles["Normal"]))
    story.append(Spacer(1, 0.3 * inch))
    story.append(Paragraph(report_text.replace("\n", "<br/>"), styles["Normal"]))

    doc.build(story)
    print(f"[pdf_generator] Report saved to {filepath}")
    return filepath


async def get_pdf_tool(mcp_servers) -> Tool:
    agent = Agent(
        name="PDFGenerator",
        instructions=f"Generates final report PDFs. Datetime: {datetime.now()}",
        model=MODEL,
        mcp_servers=mcp_servers,
    )
    return agent.as_tool(
        tool_name="PDFGenerator",
        tool_description="Generates and compiles a PDF report summarizing all analysis steps.",
        func=pdf_summary_step,
    )
