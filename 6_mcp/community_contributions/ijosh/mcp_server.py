"""
CARI ── MCP Tool Server  (run separately: python mcp_server.py)
Exposes three tools to the OpenAI Agents SDK:
  1. financial_brain        — record & categorise a transaction
  2. get_financial_summary  — fetch balance & breakdown
  3. generate_tax_report    — produce a FIRS-ready PDF
"""

import json
import os
import sys
from datetime import datetime

# ── MCP import ────────────────────────────────────────────────
from mcp.server.fastmcp import FastMCP

# ── Local imports ─────────────────────────────────────────────
sys.path.insert(0, os.path.dirname(__file__))
import database as db

# ── ReportLab ─────────────────────────────────────────────────
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_RIGHT

# ── Category maps ─────────────────────────────────────────────
EXPENSE_CATS = {
    "rent":            ["rent", "landlord", "house", "accommodation"],
    "stock/inventory": ["stock", "goods", "supply", "market", "inventory",
                        "purchase", "restock", "buy"],
    "transport":       ["fuel", "transport", "uber", "okada", "keke",
                        "bus", "logistics", "shipping"],
    "food":            ["food", "eat", "lunch", "breakfast", "dinner",
                        "restaurant", "canteen", "chop"],
    "utilities":       ["light", "nepa", "electricity", "water", "internet",
                        "generator", "diesel", "mtn", "airtel"],
    "staff/wages":     ["salary", "worker", "staff", "wage", "employee",
                        "pay worker"],
    "marketing":       ["advert", "marketing", "flyer", "promotion",
                        "social media", "print"],
    "equipment":       ["laptop", "phone", "machine", "equipment", "tool",
                        "printer"],
}
INCOME_CATS = {
    "sales":             ["sell", "sold", "sale", "customer", "revenue",
                          "sold goods", "pay me", "paid me"],
    "service income":    ["service", "job", "work done", "fix", "repair",
                          "consulting", "freelance"],
    "transfer received": ["transfer", "sent me", "credit", "received"],
    "investment return": ["dividend", "interest", "return", "profit share"],
}


def _categorise(description: str, tx_type: str) -> str:
    desc = description.lower()
    cats = INCOME_CATS if tx_type == "income" else EXPENSE_CATS
    for cat, kws in cats.items():
        if any(kw in desc for kw in kws):
            return cat
    return "other income" if tx_type == "income" else "other expense"


# ── Base directory (used for absolute PDF paths) ──────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# ── MCP Server ────────────────────────────────────────────────
mcp = FastMCP("CARI-Tools")


@mcp.tool()
async def financial_brain(
    user_id: str,
    description: str,
    amount: float,
    transaction_type: str,
) -> str:
    """
    Record and categorise a financial transaction for an SME owner.
    Call this whenever the user mentions money received (income/sales)
    or money spent (expense/payment).

    Args:
        user_id:          Session identifier for the user.
        description:      Raw transaction description in the user's own words.
        amount:           Amount in Naira as a plain number (no ₦ symbol).
        transaction_type: Exactly 'income' or 'expense'.
    """
    if transaction_type not in ("income", "expense"):
        return json.dumps({"error": "transaction_type must be 'income' or 'expense'"})

    if not db.get_user(user_id):
        db.upsert_user(user_id, "My Business")

    category = _categorise(description, transaction_type)
    tx_id    = db.save_transaction(user_id, description, amount,
                                   transaction_type, category)
    summary  = db.get_summary(user_id)

    return json.dumps({
        "status":         "✅ Recorded",
        "transaction_id": tx_id,
        "category":       category,
        "type":           transaction_type,
        "amount":         f"₦{amount:,.2f}",
        "total_income":   f"₦{summary['total_income']:,.2f}",
        "total_expenses": f"₦{summary['total_expense']:,.2f}",
        "net_balance":    f"₦{summary['net_balance']:,.2f}",
    }, ensure_ascii=False)


@mcp.tool()
async def get_financial_summary(user_id: str, month: str = "") -> str:
    """
    Retrieve the financial summary (totals, breakdown, recent transactions)
    for a user. Use when the user asks for their balance, summary, or overview.

    Args:
        user_id: Session identifier for the user.
        month:   Period in YYYY-MM format. Leave blank for current month.
    """
    summary = db.get_summary(user_id, month or None)

    if not summary["breakdown"]:
        return json.dumps({
            "message": "No transactions found for this period.",
            "period":  summary["period"],
        })

    return json.dumps({
        "period":         summary["period"],
        "total_income":   f"₦{summary['total_income']:,.2f}",
        "total_expenses": f"₦{summary['total_expense']:,.2f}",
        "net_balance":    f"₦{summary['net_balance']:,.2f}",
        "breakdown":      summary["breakdown"],
        "recent_transactions": [
            {
                "date":        t["date"],
                "description": t["description"],
                "amount":      f"₦{t['amount']:,.2f}",
                "type":        t["type"],
                "category":    t["category"],
            }
            for t in summary["recent_tx"]
        ],
    }, ensure_ascii=False)


@mcp.tool()
async def generate_tax_report(user_id: str, business_name: str) -> str:
    """
    Generate a professional FIRS-ready PDF tax summary for the current month.
    Call this when the user requests a tax report, tax summary, or FIRS filing.

    Args:
        user_id:       Session identifier for the user.
        business_name: Trading name of the SME.
    """
    summary = db.get_summary(user_id)
    period  = summary["period"]

    if not summary["breakdown"]:
        return json.dumps({
            "status":  "⚠️ No transactions",
            "message": "Please record some transactions first.",
        })

    total_income  = summary["total_income"]
    total_expense = summary["total_expense"]
    net_profit    = summary["net_balance"]
    vat_payable   = total_income * 0.075          # Nigeria VAT 7.5 %
    cit_estimate  = max(net_profit * 0.20, 0)     # SME CIT 20 %

    # ── Build PDF ─────────────────────────────────────────────
    tax_dir = os.path.join(BASE_DIR, "tax_reports")
    os.makedirs(tax_dir, exist_ok=True)
    filepath = os.path.join(tax_dir, f"CARI_Tax_{user_id}_{period}.pdf")

    GREEN  = colors.HexColor("#00A651")
    DKGRAY = colors.HexColor("#1E1E2E")
    WHITE  = colors.white
    LGRAY  = colors.HexColor("#F4F4F8")

    doc    = SimpleDocTemplate(
        filepath, pagesize=A4,
        leftMargin=20*mm, rightMargin=20*mm,
        topMargin=15*mm, bottomMargin=15*mm
    )
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "CARITitle",
        parent=styles["Normal"],
        fontSize=22, textColor=WHITE,
        fontName="Helvetica-Bold",
        alignment=TA_CENTER, spaceAfter=4,
    )
    sub_style = ParagraphStyle(
        "CARISub",
        parent=styles["Normal"],
        fontSize=10, textColor=colors.HexColor("#CCCCCC"),
        fontName="Helvetica", alignment=TA_CENTER,
    )
    label_style = ParagraphStyle(
        "Label",
        parent=styles["Normal"],
        fontSize=9, textColor=colors.HexColor("#666666"),
        fontName="Helvetica",
    )
    footer_style = ParagraphStyle(
        "Footer",
        parent=styles["Normal"],
        fontSize=8, textColor=colors.HexColor("#999999"),
        fontName="Helvetica-Oblique", alignment=TA_CENTER,
    )

    story = []

    # Header banner
    header_data = [[
        Paragraph(f"CARI — Tax Summary Report", title_style),
    ]]
    header_table = Table(header_data, colWidths=[170*mm])
    header_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), DKGRAY),
        ("TOPPADDING",    (0, 0), (-1, -1), 14),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 14),
    ]))
    story.append(header_table)
    story.append(Spacer(1, 4*mm))

    # Sub-header info
    info_data = [[
        Paragraph(f"<b>Business:</b> {business_name}", label_style),
        Paragraph(f"<b>Period:</b> {period}", label_style),
        Paragraph(f"<b>Generated:</b> {datetime.now().strftime('%d %b %Y')}", label_style),
    ]]
    info_table = Table(info_data, colWidths=[57*mm, 57*mm, 56*mm])
    info_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), LGRAY),
        ("TOPPADDING",    (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("LEFTPADDING",   (0, 0), (-1, -1), 10),
    ]))
    story.append(info_table)
    story.append(Spacer(1, 6*mm))

    # Summary KPI cards
    kpi_data = [
        [
            Paragraph("TOTAL INCOME", label_style),
            Paragraph("TOTAL EXPENSES", label_style),
            Paragraph("NET PROFIT", label_style),
        ],
        [
            Paragraph(f"<b>₦{total_income:,.2f}</b>", ParagraphStyle(
                "KPI", parent=styles["Normal"],
                fontSize=14, textColor=GREEN, fontName="Helvetica-Bold")),
            Paragraph(f"<b>₦{total_expense:,.2f}</b>", ParagraphStyle(
                "KPI2", parent=styles["Normal"],
                fontSize=14, textColor=colors.HexColor("#E74C3C"),
                fontName="Helvetica-Bold")),
            Paragraph(f"<b>₦{net_profit:,.2f}</b>", ParagraphStyle(
                "KPI3", parent=styles["Normal"],
                fontSize=14,
                textColor=GREEN if net_profit >= 0 else colors.HexColor("#E74C3C"),
                fontName="Helvetica-Bold")),
        ],
    ]
    kpi_table = Table(kpi_data, colWidths=[57*mm, 57*mm, 56*mm])
    kpi_table.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), WHITE),
        ("BOX",           (0, 0), (-1, -1), 0.5, colors.HexColor("#DDDDDD")),
        ("GRID",          (0, 0), (-1, -1), 0.5, colors.HexColor("#EEEEEE")),
        ("TOPPADDING",    (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ("LEFTPADDING",   (0, 0), (-1, -1), 12),
    ]))
    story.append(kpi_table)
    story.append(Spacer(1, 6*mm))

    # Tax liabilities
    tax_data = [
        ["Tax Type", "Base", "Rate", "Amount Due"],
        ["VAT (Value Added Tax)",
         f"₦{total_income:,.2f}", "7.5%", f"₦{vat_payable:,.2f}"],
        ["Company Income Tax (SME)",
         f"₦{net_profit:,.2f}", "20.0%", f"₦{cit_estimate:,.2f}"],
        ["TOTAL TAX LIABILITY", "", "",
         f"₦{vat_payable + cit_estimate:,.2f}"],
    ]
    tax_table = Table(tax_data, colWidths=[75*mm, 40*mm, 20*mm, 35*mm])
    tax_table.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1,  0), DKGRAY),
        ("TEXTCOLOR",     (0, 0), (-1,  0), WHITE),
        ("FONTNAME",      (0, 0), (-1,  0), "Helvetica-Bold"),
        ("BACKGROUND",    (0, -1), (-1, -1), GREEN),
        ("TEXTCOLOR",     (0, -1), (-1, -1), WHITE),
        ("FONTNAME",      (0, -1), (-1, -1), "Helvetica-Bold"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -2), [WHITE, LGRAY]),
        ("GRID",          (0, 0), (-1, -1), 0.5, colors.HexColor("#CCCCCC")),
        ("TOPPADDING",    (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("LEFTPADDING",   (0, 0), (-1, -1), 10),
        ("FONTSIZE",      (0, 0), (-1, -1), 9),
    ]))
    story.append(Paragraph("<b>TAX LIABILITIES</b>", ParagraphStyle(
        "SectionHead", parent=styles["Normal"],
        fontSize=11, textColor=DKGRAY, fontName="Helvetica-Bold",
        spaceBefore=4, spaceAfter=4)))
    story.append(tax_table)
    story.append(Spacer(1, 6*mm))

    # Category breakdown
    if summary["breakdown"]:
        story.append(Paragraph("<b>TRANSACTION BREAKDOWN</b>", ParagraphStyle(
            "SectionHead2", parent=styles["Normal"],
            fontSize=11, textColor=DKGRAY, fontName="Helvetica-Bold",
            spaceBefore=4, spaceAfter=4)))
        bk_data = [["Type", "Category", "Transactions", "Total"]]
        for r in summary["breakdown"]:
            bk_data.append([
                r["type"].title(), r["category"].title(),
                str(r["cnt"]), f"₦{r['total']:,.2f}"
            ])
        bk_table = Table(bk_data, colWidths=[30*mm, 75*mm, 30*mm, 35*mm])
        bk_table.setStyle(TableStyle([
            ("BACKGROUND",    (0, 0), (-1,  0), colors.HexColor("#2D2D44")),
            ("TEXTCOLOR",     (0, 0), (-1,  0), WHITE),
            ("FONTNAME",      (0, 0), (-1,  0), "Helvetica-Bold"),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, LGRAY]),
            ("GRID",          (0, 0), (-1, -1), 0.5, colors.HexColor("#DDDDDD")),
            ("TOPPADDING",    (0, 0), (-1, -1), 7),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
            ("LEFTPADDING",   (0, 0), (-1, -1), 10),
            ("FONTSIZE",      (0, 0), (-1, -1), 9),
        ]))
        story.append(bk_table)

    story.append(Spacer(1, 8*mm))
    story.append(Paragraph(
        "Generated by CARI — Your AI-Powered CFO Agent  •  "
        "For FIRS submission via TaxPro Max portal or your nearest tax office.",
        footer_style
    ))

    doc.build(story)

    return json.dumps({
        "status":        "✅ PDF generated",
        "pdf_path":      filepath,
        "period":        period,
        "total_income":  f"₦{total_income:,.2f}",
        "vat_payable":   f"₦{vat_payable:,.2f}",
        "cit_estimate":  f"₦{cit_estimate:,.2f}",
        "total_tax":     f"₦{vat_payable + cit_estimate:,.2f}",
        "firs_note":     "Upload to TaxPro Max or present at nearest FIRS office.",
    }, ensure_ascii=False)


if __name__ == "__main__":
    db.init_db()
    print("🚀 CARI MCP Tool Server starting on http://localhost:8000 ...")
    mcp = FastMCP("CARI-Tools", host="127.0.0.1", port=8000)
    mcp.run(transport="streamable-http")
