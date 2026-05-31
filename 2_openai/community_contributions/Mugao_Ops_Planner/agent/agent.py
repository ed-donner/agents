from utils.logger import log


class Agent:

    def __init__(self, planner, client):
        self.planner = planner
        self.client = client

    def run(self, query: str):
        log("Agent started")

        plan = self.planner.create_plan(query)
        log(f"Plan: {plan}")

        data = {
            "schedule": None,
            "budget": None,
            "priorities": None,
            "summary": None
        }

        sample_tasks = ["Finish report", "Gym", "Read book", "Email client"]
        sample_expenses = {
            "rent": 500,
            "food": 200,
            "transport": 100
        }

        for step in plan:

            if step == "schedule_week":
                data["schedule"] = self.client.call(
                    "schedule_week", {"goal": query}
                )

            elif step == "calculate_budget":
                data["budget"] = self.client.call(
                    "calculate_budget", {"expenses": sample_expenses}
                )

            elif step == "prioritize_tasks":
                data["priorities"] = self.client.call(
                    "prioritize_tasks", {"tasks": sample_tasks}
                )

            elif step == "summarize":
                data["summary"] = self.client.call(
                    "summarize", {"data": data}
                )

            elif step == "format_output":
                return self.client.call(
                    "format_output",
                    {"goal": query, "data": data}
                )

        return data