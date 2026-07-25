"""
CARI ── MCP Tool Server  (run separately: python mcp_server.py)
Exposes three tools to the OpenAI Agents SDK:
  1. financial_brain        — record & categorise a transaction
  2. get_financial_summary  — fetch balance & breakdown
  3. generate_tax_report    — produce a FIRS-ready PDF
"""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime

from mcp.server.fastmcp import FastMCP

sys.path.insert(0, os.path.dirname(__file__))
import database as db

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER

EXPENSE_CATS = {
    "rent": ["rent", "landlord", "house", "accommodation"],
    "stock/inventory": ["stock", "goods", "supply", "market", "inventory", "purchase", "restock", "buy"],
    "transport": ["fuel", "transport", "uber", "okada", "keke", "bus", "logistics", "shipping"],
    "food": ["food", "eat", "lunch", "breakfast", "dinner", "restaurant", "canteen", "chop"],
    "utilities": ["light", "nepa", "electricity", "water", "internet", "generator", "diesel", "mtn", "airtel"],
    "staff/wages": ["salary", "worker", "staff", "wage", "employee", "pay worker"],
    "marketing": ["advert", "marketing", "flyer", "promotion", "social media", "print"],
    "equipment": ["laptop", "phone", "machine", "equipment", "tool", "printer"],
}
INCOME_CATS = {
    "sales": ["sell", "sold", "sale", "customer", "revenue", "sold goods", "pay me", "paid me"],
    "service income": ["service", "job", "work done", "fix", "repair", "consulting", "freelance"],
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


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
mcp = FastMCP("CARI-Tools")


@mcp.tool()
async def financial_brain(user_id: str, description: str, amount: float, transaction_type: str) -> str:
    if transaction_type not in ("income", "expense"):
        return json.dumps({"error": "transaction_type must be 'income' or 'expense'"})

    if not db.get_user(user_id):
        db.upsert_user(user_id, "My Business")

    category = _categorise(description, transaction_type)
    tx_id = db.save_transaction(user_id, description, amount, transaction_type, category)
    summary = db.get_summary(user_id)

    return json.dumps(
        {
            "status": "✅ Recorded",
            "transaction_id": tx_id,
            "category": category,
            "type": transaction_type,
            "amount": f"₦{amount:,.2f}",
            "total_income": f"₦{summary['total_income']:,.2f}",
            "total_expenses": f"₦{summary['total_expense']:,.2f}",
            "net_balance": f"₦{summary['net_balance']:,.2f}",
        },
        ensure_ascii=False,
    )


@mcp.tool()
async def get_financial_summary(user_id: str, month: str = "") -> str:
    summary = db.get_summary(user_id, month or None)

    if not summary["breakdown"]:
        return json.dumps({"message": "No transactions found for this period.", "period": summary["period"]})

    return json.dumps(
        {
            "period": summary["period"],
            "total_income": f"₦{summary['total_income']:,.2f}",
            "total_expenses": f"₦{summary['total_expense']:,.2f}",
            "net_balance": f"₦{summary['net_balance']:,.2f}",
            "breakdown": summary["breakdown"],
            "recent_transactions": [
                {
                    "date": t["date"],
                    "description": t["description"],
                    "amount": f"₦{t['amount']:,.2f}",
                    "type": t["type"],
                    "category": t["category"],
                }
                for t in summary["recent_tx"]
            ],
        },
        ensure_ascii=False,
    )


@mcp.tool()
async def generate_tax_report(user_id: str, business_name: str) -> str:
    summary = db.get_summary(user_id)
    period = summary["period"]

    if not summary["breakdown"]:
        return json.dumps(
            {"status": "⚠️ No transactions", "message": "Please record some transactions first."},
            ensure_ascii=False,
        )

    total_income = summary["total_income"]
    total_expense = summary["total_expense"]
    net_profit = summary["net_balance"]
    vat_payable = total_income * 0.075
    cit_estimate = max(net_profit * 0.20, 0)

    tax_dir = os.path.join(BASE_DIR, "tax_reports")
    os.makedirs(tax_dir, exist_ok=True)
    filepath = os.path.join(tax_dir, f"CARI_Tax_{user_id}_{period}.pdf")

    GREEN = colors.HexColor("#00A651")
    DKGRAY = colors.HexColor("#1E1E2E")
    WHITE = colors.white
    LGRAY = colors.HexColor("#F4F4F8")

    doc = SimpleDocTemplate(filepath, pagesize=A4, leftMargin=20 * mm, rightMargin=20 * mm, topMargin=15 * mm, bottomMargin=15 * mm)
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle("CARITitle", parent=styles["Normal"], fontSize=22, textColor=WHITE, fontName="Helvetica-Bold", alignment=TA_CENTER, spaceAfter=4)
    label_style = ParagraphStyle("Label", parent=styles["Normal"], fontSize=9, textColor=colors.HexColor("#666666"), fontName="Helvetica")
    footer_style = ParagraphStyle("Footer", parent=styles["Normal"], fontSize=8, textColor=colors.HexColor("#999999"), fontName="Helvetica-Oblique", alignment=TA_CENTER)

    story = []
    header_table = Table([[Paragraph("CARI — Tax Summary Report", title_style)]], colWidths=[170 * mm])
    header_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), DKGRAY),
        ("TOPPADDING", (0, 0), (-1, -1), 14),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 14),
    ]))
    story.extend([header_table, Spacer(1, 4 * mm)])

    info_table = Table([[
        Paragraph(f"<b>Business:</b> {business_name}", label_style),
        Paragraph(f"<b>Period:</b> {period}", label_style),
        Paragraph(f"<b>Generated:</b> {datetime.now().strftime('%d %b %Y')}", label_style),
    ]], colWidths=[57 * mm, 57 * mm, 56 * mm])
    info_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), LGRAY),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
    ]))
    story.extend([info_table, Spacer(1, 6 * mm)])

    kpi_table = Table([
        [Paragraph("TOTAL INCOME", label_style), Paragraph("TOTAL EXPENSES", label_style), Paragraph("NET PROFIT", label_style)],
        [
            Paragraph(f"<b>₦{total_income:,.2f}</b>", ParagraphStyle("KPI", parent=styles["Normal"], fontSize=14, textColor=GREEN, fontName="Helvetica-Bold")),
            Paragraph(f"<b>₦{total_expense:,.2f}</b>", ParagraphStyle("KPI2", parent=styles["Normal"], fontSize=14, textColor=colors.HexColor("#E74C3C"), fontName="Helvetica-Bold")),
            Paragraph(f"<b>₦{net_profit:,.2f}</b>", ParagraphStyle("KPI3", parent=styles["Normal"], fontSize=14, textColor=GREEN if net_profit >= 0 else colors.HexColor("#E74C3C"), fontName="Helvetica-Bold")),
        ],
    ], colWidths=[57 * mm, 57 * mm, 56 * mm])
    kpi_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), WHITE),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#DDDDDD")),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#EEEEEE")),
        ("TOPPADDING", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ("LEFTPADDING", (0, 0), (-1, -1), 12),
    ]))
    story.extend([kpi_table, Spacer(1, 6 * mm)])

    tax_table = Table([
        ["Tax Type", "Base", "Rate", "Amount Due"],
        ["VAT (Value Added Tax)", f"₦{total_income:,.2f}", "7.5%", f"₦{vat_payable:,.2f}"],
        ["Company Income Tax (SME)", f"₦{net_profit:,.2f}", "20.0%", f"₦{cit_estimate:,.2f}"],
        ["TOTAL TAX LIABILITY", "", "", f"₦{vat_payable + cit_estimate:,.2f}"],
    ], colWidths=[75 * mm, 40 * mm, 20 * mm, 35 * mm])
    tax_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), DKGRAY),
        ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("BACKGROUND", (0, -1), (-1, -1), GREEN),
        ("TEXTCOLOR", (0, -1), (-1, -1), WHITE),
        ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -2), [WHITE, LGRAY]),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CCCCCC")),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
    ]))
    story.append(Paragraph("<b>TAX LIABILITIES</b>", ParagraphStyle("SectionHead", parent=styles["Normal"], fontSize=11, textColor=DKGRAY, fontName="Helvetica-Bold", spaceBefore=4, spaceAfter=4)))
    story.extend([tax_table, Spacer(1, 6 * mm)])

    if summary["breakdown"]:
        story.append(Paragraph("<b>TRANSACTION BREAKDOWN</b>", ParagraphStyle("SectionHead2", parent=styles["Normal"], fontSize=11, textColor=DKGRAY, fontName="Helvetica-Bold", spaceBefore=4, spaceAfter=4)))
        bk_data = [["Type", "Category", "Transactions", "Total"]]
        for r in summary["breakdown"]:
            bk_data.append([r["type"].title(), r["category"].title(), str(r["cnt"]), f"₦{r['total']:,.2f}"])
        bk_table = Table(bk_data, colWidths=[30 * mm, 75 * mm, 30 * mm, 35 * mm])
        bk_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2D2D44")),
            ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, LGRAY]),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#DDDDDD")),
            ("TOPPADDING", (0, 0), (-1, -1), 7),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
            ("LEFTPADDING", (0, 0), (-1, -1), 10),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
        ]))
        story.append(bk_table)

    story.extend([
        Spacer(1, 8 * mm),
        Paragraph(
            "Generated by CARI — Your AI-Powered CFO Agent  •  For FIRS submission via TaxPro Max portal or your nearest tax office.",
            footer_style,
        ),
    ])

    doc.build(story)

    return json.dumps(
        {
            "status": "✅ PDF generated",
            "pdf_path": filepath,
            "period": period,
            "total_income": f"₦{total_income:,.2f}",
            "vat_payable": f"₦{vat_payable:,.2f}",
            "cit_estimate": f"₦{cit_estimate:,.2f}",
            "total_tax": f"₦{vat_payable + cit_estimate:,.2f}",
            "firs_note": "Upload to TaxPro Max or present at nearest FIRS office.",
        },
        ensure_ascii=False,
    )


if __name__ == "__main__":
    db.init_db()
    print("🚀 CARI MCP Tool Server starting on http://127.0.0.1:8000 ...")
    mcp.settings.host = "127.0.0.1"
    mcp.settings.port = 8000
    mcp.run(transport="streamable-http")
