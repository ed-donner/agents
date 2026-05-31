import json
from datetime import datetime
from finance_db import (
    write_transaction,
    read_transactions,
    write_budget,
    read_budgets,
    get_spending_by_category,
    get_totals,
)

DEFAULT_CATEGORIES = [
    "Food", "Transport", "Housing", "Utilities",
    "Entertainment", "Shopping", "Health", "Education", "Other",
]


class FinanceAccount:

    def __init__(self, name: str):
        self.name = name.lower()

    def add_expense(self, amount: float, category: str, description: str) -> str:
        if amount <= 0:
            raise ValueError("Expense amount must be positive.")
        txn_id = write_transaction(self.name, amount, category, description, "expense")
        return json.dumps({
            "status": "ok",
            "id": txn_id,
            "message": f"Recorded ${amount:.2f} expense in {category}",
        })

    def add_income(self, amount: float, source: str, description: str) -> str:
        if amount <= 0:
            raise ValueError("Income amount must be positive.")
        txn_id = write_transaction(self.name, amount, source, description, "income")
        return json.dumps({
            "status": "ok",
            "id": txn_id,
            "message": f"Recorded ${amount:.2f} income from {source}",
        })

    def list_transactions(self, category: str = "", month: str = "") -> str:
        txns = read_transactions(self.name, category=category, month=month)
        if not txns:
            return json.dumps({"transactions": [], "message": "No transactions found."})
        return json.dumps({"transactions": txns, "count": len(txns)})

    def get_summary(self, month: str = "") -> str:
        totals = get_totals(self.name, month=month)
        by_category = get_spending_by_category(self.name, month=month)
        period = month if month else "all time"
        return json.dumps({
            "period": period,
            "total_income": totals["income"],
            "total_expenses": totals["expenses"],
            "net": totals["net"],
            "spending_by_category": by_category,
        })

    def set_budget(self, category: str, amount: float) -> str:
        if amount <= 0:
            raise ValueError("Budget amount must be positive.")
        write_budget(self.name, category, amount)
        return json.dumps({
            "status": "ok",
            "message": f"Budget for {category} set to ${amount:.2f}",
        })

    def budget_status(self) -> str:
        budgets = read_budgets(self.name)
        if not budgets:
            return json.dumps({"message": "No budgets set.", "budgets": {}})

        current_month = datetime.now().strftime("%Y-%m")
        spending = get_spending_by_category(self.name, month=current_month)

        status = {}
        for category, limit in budgets.items():
            spent = spending.get(category, 0.0)
            remaining = limit - spent
            status[category] = {
                "budget": limit,
                "spent": spent,
                "remaining": remaining,
                "over_budget": remaining < 0,
            }

        return json.dumps({"month": current_month, "budgets": status})
