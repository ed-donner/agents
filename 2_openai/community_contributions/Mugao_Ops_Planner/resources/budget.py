def calculate_budget(expenses: dict):
    total = sum(expenses.values())

    breakdown = {
        "total": total,
        "details": expenses
    }

    return breakdown