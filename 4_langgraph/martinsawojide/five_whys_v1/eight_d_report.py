"""
eight_d_report.py
-----------------
AIAG 8D (Eight Disciplines Problem Solving) report generator.

Two responsibilities:
1. EightDContent — Pydantic schema + LLM population: fills in the 8D fields
   that are not directly in the investigation State (D3, D6, D7, D8) using an
   LLM call, and maps the investigation tree into D4/D5.

2. generate_pdf() — produces a professionally formatted PDF using fpdf2.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from fpdf import FPDF
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

from models import WhyNode


# ---------------------------------------------------------------------------
# 8D content schema
# ---------------------------------------------------------------------------

class EightDContent(BaseModel):
    """All content for an AIAG 8D report, ready to be rendered to PDF."""

    # Investigation metadata
    investigation_id: str
    phenomenon: str
    domain_context: str
    report_date: str

    # D1 — Team
    team_leader: str = Field(default="[To be assigned]")
    team_members: str = Field(default="[To be assigned]")
    champion: str = Field(default="[To be assigned]")

    # D2 — Problem Description (IS / IS NOT)
    problem_is: str = Field(description="What IS happening — precise description of the problem")
    problem_is_not: str = Field(description="What is NOT happening — helps bound the problem")
    when_first_observed: str = Field(default="[As reported]")
    where_observed: str = Field(description="Location / process / equipment where observed")
    magnitude: str = Field(description="How big / how often / what impact")

    # D3 — Interim Containment Actions
    containment_actions: str = Field(
        description="Immediate short-term actions taken to protect the process / "
                    "customer while the permanent fix is implemented"
    )
    containment_effectiveness: str = Field(
        description="How effectiveness of containment will be verified"
    )

    # D4 — Root Cause(s) — populated from investigation tree
    root_causes_summary: str = Field(
        description="Summary of verified root cause(s) from the 5 Whys investigation"
    )
    escape_point: str = Field(
        description="Why was this root cause not detected / prevented earlier?"
    )

    # D5 — Permanent Corrective Actions — populated from countermeasures
    corrective_actions_summary: str = Field(
        description="Summary of permanent corrective actions and their owners"
    )

    # D6 — Implementation & Verification
    implementation_plan: str = Field(
        description="Who does what by when to implement the D5 corrective actions"
    )
    verification_method: str = Field(
        description="How effectiveness of corrective actions will be measured and verified"
    )

    # D7 — Prevent Recurrence
    systemic_prevention: str = Field(
        description="Systemic changes to prevent recurrence: updated procedures, "
                    "standards, training, error-proofing (poka-yoke)"
    )
    lessons_learned: str = Field(
        description="Key lessons learned that should be shared across similar processes"
    )

    # D8 — Team Recognition
    recognition_note: str = Field(
        default="The team is recognized and thanked for their rigorous application "
                "of the 5 Whys methodology and commitment to root cause resolution."
    )


# ---------------------------------------------------------------------------
# LLM population
# ---------------------------------------------------------------------------

async def populate_8d_content(
    investigation_id: str,
    phenomenon: str,
    domain_context: str,
    why_nodes: list[WhyNode],
    domain: str = "manufacturing",
) -> EightDContent:
    """
    Uses an LLM to fill in the 8D fields that are not directly in the
    investigation State (D3 containment, D2 IS/IS NOT framing, D6 plan,
    D7 prevention, etc.) and maps tree data into D4/D5.
    """
    # Build D4 root causes from tree
    root_cause_nodes = [n for n in why_nodes if n.get("is_root_cause") or n.get("countermeasure")]
    if root_cause_nodes:
        d4_lines = []
        d5_lines = []
        for n in root_cause_nodes:
            d4_lines.append(
                f"- [{n['branch_path']}] {n['hypothesis']}"
                + (f"\n  Gemba notes: {n['gemba_notes']}" if n.get("gemba_notes") else "")
            )
            if n.get("countermeasure"):
                d5_lines.append(f"- {n['countermeasure']}")
        root_causes_summary = "\n".join(d4_lines) or "See investigation tree."
        corrective_actions_summary = "\n".join(d5_lines) or "To be determined."
    else:
        root_causes_summary = "Investigation in progress — no root causes confirmed yet."
        corrective_actions_summary = "To be determined after root cause confirmation."

    # Build investigation tree summary for LLM context
    tree_summary = "\n".join(
        f"  [{n['branch_path']}] depth={n['depth']} | {n['gemba_result']} | "
        f"{n['hypothesis']}"
        + (f" | Notes: {n['gemba_notes']}" if n.get("gemba_notes") else "")
        for n in why_nodes
    ) or "(no nodes yet)"

    system_prompt = (
        f"You are an AIAG 8D report specialist with deep expertise in {domain}.\n"
        "Based on the 5 Whys investigation provided, generate structured 8D report content.\n"
        "Be specific, actionable, and professional. Use domain-appropriate language."
    )
    user_prompt = (
        f"Investigation ID: {investigation_id}\n"
        f"Phenomenon: '{phenomenon}'\n"
        f"Domain/Context: {domain_context}\n\n"
        f"5 Whys investigation tree:\n{tree_summary}\n\n"
        f"Confirmed root causes (D4):\n{root_causes_summary}\n\n"
        f"Corrective actions (D5):\n{corrective_actions_summary}\n\n"
        "Generate the complete 8D report content. For fields not directly available "
        "(D2 IS/IS NOT framing, D3 containment, D6 implementation plan, D7 systemic "
        "prevention, escape point), use the investigation context to make reasonable, "
        "actionable recommendations."
    )

    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.2).with_structured_output(
        EightDContent
    )
    content: EightDContent = await llm.ainvoke(
        [SystemMessage(content=system_prompt), HumanMessage(content=user_prompt)]
    )

    # Ensure non-LLM fields are set correctly
    content.investigation_id = investigation_id
    content.phenomenon = phenomenon
    content.domain_context = domain_context
    content.report_date = datetime.now().strftime("%Y-%m-%d %H:%M")
    content.root_causes_summary = root_causes_summary
    content.corrective_actions_summary = corrective_actions_summary

    return content


# ---------------------------------------------------------------------------
# PDF generation
# ---------------------------------------------------------------------------

# Colour palette
_HEADER_R, _HEADER_G, _HEADER_B = 0, 51, 102        # dark navy
_SECTION_R, _SECTION_G, _SECTION_B = 0, 102, 179    # mid blue
_ALT_R, _ALT_G, _ALT_B = 230, 240, 255              # light blue row tint
_TEXT_R, _TEXT_G, _TEXT_B = 30, 30, 30              # near-black body text


class _EightDPDF(FPDF):
    """Custom FPDF subclass with shared header/footer and helper methods."""

    def __init__(self, investigation_id: str, report_date: str):
        super().__init__()
        self._inv_id = investigation_id
        self._report_date = report_date

    def header(self):
        self.set_fill_color(_HEADER_R, _HEADER_G, _HEADER_B)
        self.rect(0, 0, 210, 14, "F")
        self.set_text_color(255, 255, 255)
        self.set_font("Helvetica", "B", 11)
        self.set_xy(8, 3)
        self.cell(130, 8, "AIAG 8D Problem Solving Report", ln=False)
        self.set_font("Helvetica", "", 8)
        self.set_xy(140, 3)
        self.cell(60, 4, f"ID: {self._inv_id}", ln=False, align="R")
        self.set_xy(140, 7)
        self.cell(60, 4, self._report_date, ln=False, align="R")
        self.ln(10)

    def footer(self):
        self.set_y(-12)
        self.set_font("Helvetica", "I", 7)
        self.set_text_color(150, 150, 150)
        self.cell(0, 6, f"5 Whys Investigation Agent  |  Page {self.page_no()}", align="C")

    def section_title(self, discipline: str, title: str):
        """Render a coloured discipline banner, e.g. 'D1  Team'."""
        self.ln(3)
        self.set_fill_color(_SECTION_R, _SECTION_G, _SECTION_B)
        self.set_text_color(255, 255, 255)
        self.set_font("Helvetica", "B", 10)
        self.cell(0, 7, f"  {discipline}   {title}", ln=True, fill=True)
        self.set_text_color(_TEXT_R, _TEXT_G, _TEXT_B)
        self.ln(1)

    def field_row(self, label: str, value: str, alt: bool = False):
        """Render a two-column label / value row."""
        if alt:
            self.set_fill_color(_ALT_R, _ALT_G, _ALT_B)
            fill = True
        else:
            fill = False

        self.set_font("Helvetica", "B", 8)
        x = self.get_x()
        y = self.get_y()
        label_w = 48
        value_w = self.epw - label_w

        # Measure value height
        lines = self._count_lines(value, value_w)
        row_h = max(6, lines * 4.5)

        self.set_xy(x, y)
        if fill:
            self.set_fill_color(_ALT_R, _ALT_G, _ALT_B)
        self.multi_cell(label_w, row_h, label, border=0, fill=fill)

        self.set_font("Helvetica", "", 8)
        self.set_xy(x + label_w, y)
        self.multi_cell(value_w, row_h, value, border=0, fill=fill)
        self.ln(1)

    def body_text(self, text: str):
        self.set_font("Helvetica", "", 8.5)
        self.set_text_color(_TEXT_R, _TEXT_G, _TEXT_B)
        self.multi_cell(0, 5, text)
        self.ln(2)

    def _count_lines(self, text: str, width: float) -> int:
        """Rough line count estimate for multi_cell height calculation."""
        char_per_line = max(1, int(width / 2.1))
        lines = 0
        for para in text.split("\n"):
            lines += max(1, (len(para) // char_per_line) + 1)
        return lines


def generate_pdf(content: EightDContent, output_path: str) -> str:
    """
    Render an EightDContent object to a formatted PDF at output_path.
    Returns the output_path on success.
    """
    pdf = _EightDPDF(
        investigation_id=content.investigation_id,
        report_date=content.report_date,
    )
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)

    # ── Cover summary ───────────────────────────────────────────────────────
    pdf.set_fill_color(245, 248, 252)
    pdf.set_font("Helvetica", "B", 13)
    pdf.set_text_color(_HEADER_R, _HEADER_G, _HEADER_B)
    pdf.cell(0, 10, "8D Problem Solving Report", ln=True, fill=False)
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(_TEXT_R, _TEXT_G, _TEXT_B)
    pdf.multi_cell(0, 5, f"Phenomenon: {content.phenomenon}")
    pdf.cell(0, 5, f"Domain / Context: {content.domain_context}", ln=True)
    pdf.cell(0, 5, f"Report Date: {content.report_date}", ln=True)
    pdf.ln(3)

    # ── D1 Team ─────────────────────────────────────────────────────────────
    pdf.section_title("D1", "Team")
    pdf.field_row("Team Leader:", content.team_leader, alt=False)
    pdf.field_row("Team Members:", content.team_members, alt=True)
    pdf.field_row("Champion / Sponsor:", content.champion, alt=False)

    # ── D2 Problem Description ───────────────────────────────────────────────
    pdf.section_title("D2", "Problem Description")
    pdf.field_row("IS (what is happening):", content.problem_is, alt=False)
    pdf.field_row("IS NOT (what is not):", content.problem_is_not, alt=True)
    pdf.field_row("First Observed:", content.when_first_observed, alt=False)
    pdf.field_row("Location / Equipment:", content.where_observed, alt=True)
    pdf.field_row("Magnitude / Impact:", content.magnitude, alt=False)

    # ── D3 Interim Containment ────────────────────────────────────────────────
    pdf.section_title("D3", "Interim Containment Actions")
    pdf.field_row("Containment Actions:", content.containment_actions, alt=False)
    pdf.field_row("Verification Method:", content.containment_effectiveness, alt=True)

    # ── D4 Root Cause ────────────────────────────────────────────────────────
    pdf.section_title("D4", "Root Cause Analysis (5 Whys)")
    pdf.body_text(content.root_causes_summary)
    pdf.field_row("Escape Point:", content.escape_point, alt=True)

    # ── D5 Corrective Actions ────────────────────────────────────────────────
    pdf.section_title("D5", "Permanent Corrective Actions")
    pdf.body_text(content.corrective_actions_summary)

    # ── D6 Implementation & Verification ─────────────────────────────────────
    pdf.section_title("D6", "Implementation & Verification")
    pdf.field_row("Implementation Plan:", content.implementation_plan, alt=False)
    pdf.field_row("Verification Method:", content.verification_method, alt=True)

    # ── D7 Prevent Recurrence ────────────────────────────────────────────────
    pdf.section_title("D7", "Prevent Recurrence")
    pdf.field_row("Systemic Prevention:", content.systemic_prevention, alt=False)
    pdf.field_row("Lessons Learned:", content.lessons_learned, alt=True)

    # ── D8 Team Recognition ───────────────────────────────────────────────────
    pdf.section_title("D8", "Team Recognition")
    pdf.body_text(content.recognition_note)
    pdf.ln(4)
    pdf.set_font("Helvetica", "I", 8)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 5, f"Report generated by 5 Whys Investigation Agent  —  {content.report_date}", ln=True)

    pdf.output(output_path)
    return output_path
