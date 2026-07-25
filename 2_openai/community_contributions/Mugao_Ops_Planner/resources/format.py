def format_output(goal: str, data: dict):
    return {
        "goal": goal,
        "schedule": data.get("schedule"),
        "budget": data.get("budget"),
        "priorities": data.get("priorities"),
        "summary": data.get("summary")
    }