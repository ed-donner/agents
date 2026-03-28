class Planner:

    def create_plan(self, query: str):
        q = query.lower()
        plan = []

        if "plan" in q or "week" in q:
            plan.append("schedule_week")

        if "budget" in q or "expense" in q:
            plan.append("calculate_budget")

        if "prioritize" in q or "tasks" in q:
            plan.append("prioritize_tasks")

        plan.append("summarize")
        plan.append("format_output")

        return plan