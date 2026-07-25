"""MCP server: track expenses, extract text from bank-statement PDFs, surface simple savings insights."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel, Field
from pypdf import PdfReader

_ROOT = Path(__file__).resolve().parent
DB_PATH = _ROOT / "expenses.db"
PDF_DIR = _ROOT / "bank_pdfs"
CATEGORIES_PATH = _ROOT / "categories.json"

mcp = FastMCP("expense_bank_server")


def _init_db() -> None:
    PDF_DIR.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS expenses(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                amount REAL NOT NULL,
                category TEXT NOT NULL,
                subcategory TEXT DEFAULT '',
                note TEXT DEFAULT ''
            )
            """
        )


_init_db()


class AddExpenseArgs(BaseModel):
    date: str = Field(description="ISO date YYYY-MM-DD")
    amount: float = Field(description="Positive number for spending")
    category: str = Field(description="Top-level category e.g. food, transport, housing")
    subcategory: str = Field(default="", description="Optional subcategory")
    note: str = Field(default="", description="Merchant or memo")


@mcp.tool()
def add_expense(args: AddExpenseArgs) -> str:
    """Insert one expense row (e.g. after parsing a bank PDF or manual entry)."""
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            "INSERT INTO expenses(date, amount, category, subcategory, note) VALUES (?,?,?,?,?)",
            (args.date, args.amount, args.category, args.subcategory, args.note),
        )
        conn.commit()
    return "ok"


@mcp.tool()
def list_expenses(start_date: str, end_date: str) -> str:
    """List expenses in an inclusive date range as JSON."""
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.execute(
            """
            SELECT id, date, amount, category, subcategory, note
            FROM expenses
            WHERE date BETWEEN ? AND ?
            ORDER BY date ASC, id ASC
            """,
            (start_date, end_date),
        )
        cols = [d[0] for d in cur.description]
        rows = [dict(zip(cols, r)) for r in cur.fetchall()]
    return json.dumps(rows, indent=2)


@mcp.tool()
def summarize_by_category(start_date: str, end_date: str) -> str:
    """Sum amounts grouped by category (JSON)."""
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.execute(
            """
            SELECT category, SUM(amount) AS total
            FROM expenses
            WHERE date BETWEEN ? AND ?
            GROUP BY category
            ORDER BY total DESC
            """,
            (start_date, end_date),
        )
        rows = [{"category": r[0], "total": round(r[1], 2)} for r in cur.fetchall()]
    return json.dumps(rows, indent=2)


@mcp.tool()
def list_bank_pdfs() -> str:
    """List PDF filenames in bank_pdfs/ (drop copy-only exports from your bank here)."""
    if not PDF_DIR.is_dir():
        return json.dumps([])
    names = sorted(p.name for p in PDF_DIR.iterdir() if p.suffix.lower() == ".pdf")
    return json.dumps(names, indent=2)


class PdfNameArgs(BaseModel):
    filename: str = Field(
        description="Basename only, e.g. statement_march.pdf — must exist in bank_pdfs/"
    )


@mcp.tool()
def extract_bank_pdf_text(args: PdfNameArgs) -> str:
    """Extract plain text from a PDF in bank_pdfs/ for the model to parse transactions."""
    name = Path(args.filename).name
    if name != args.filename or ".." in args.filename:
        return "error: use a plain filename only (no paths)"
    path = PDF_DIR / name
    if not path.is_file():
        return f"error: {name} not found in bank_pdfs — use list_bank_pdfs first"
    reader = PdfReader(str(path))
    parts: list[str] = []
    for page in reader.pages:
        parts.append(page.extract_text() or "")
    text = "\n".join(parts).strip()
    if len(text) > 120_000:
        text = text[:120_000] + "\n...[truncated]"
    return text or "(no text extracted — PDF may be image-only or encrypted)"


@mcp.tool()
def compute_insights(start_date: str, end_date: str) -> str:
    """Return category totals, overspend flags (e.g. food), and heuristic monthly savings ideas."""
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.execute(
            """
            SELECT category, SUM(amount) AS total
            FROM expenses
            WHERE date BETWEEN ? AND ?
            GROUP BY category
            """,
            (start_date, end_date),
        )
        by_cat = {row[0]: float(row[1]) for row in cur.fetchall()}
    total = sum(by_cat.values())
    food_bucket = (
        by_cat.get("food", 0.0)
        + by_cat.get("dining_out", 0.0)
        + by_cat.get("fast_food", 0.0)
        + by_cat.get("coffee_tea", 0.0)
    )

    insights: dict = {
        "period": {"start": start_date, "end": end_date},
        "total_spending": round(total, 2),
        "by_category": {k: round(v, 2) for k, v in sorted(by_cat.items(), key=lambda x: -x[1])},
        "flags": [],
        "savings_ideas": [],
    }

    if total <= 0:
        insights["note"] = "No expenses in range — add expenses or import from a PDF."
        return json.dumps(insights, indent=2)

    food_share = food_bucket / total
    if food_share > 0.28:
        insights["flags"].append(
            {
                "type": "overspend_food",
                "message": "Food-related categories make up a large share of spending this period.",
                "food_bucket_percent": round(100 * food_share, 1),
            }
        )

    # Heuristic: cutting food bucket by 20%
    cut = food_bucket * 0.20
    if cut >= 25:
        insights["savings_ideas"].append(
            {
                "type": "reduce_food_20pct",
                "message": f"If you reduced food/dining spending by about 20%, you could free roughly ${cut:.0f}/month (same period length).",
                "estimated_monthly_equivalent": round(cut, 2),
            }
        )

    # Generic top category
    top_cat, top_amt = max(by_cat.items(), key=lambda x: x[1])
    if top_amt / total > 0.35 and top_cat in ("shopping", "entertainment", "food", "dining_out"):
        insights["flags"].append(
            {
                "type": "concentrated_spending",
                "message": f"A large portion of spending is in “{top_cat}” — worth reviewing subscriptions and discretionary buys.",
                "top_category": top_cat,
                "top_category_percent": round(100 * top_amt / total, 1),
            }
        )

    return json.dumps(insights, indent=2)


@mcp.resource("expense://categories", mime_type="application/json")
async def categories_resource() -> str:
    if CATEGORIES_PATH.is_file():
        return CATEGORIES_PATH.read_text(encoding="utf-8")
    return json.dumps({"food": ["groceries", "dining_out"], "transport": ["fuel", "public_transport"]})


if __name__ == "__main__":
    mcp.run(transport="stdio")
