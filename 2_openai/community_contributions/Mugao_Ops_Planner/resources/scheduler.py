def create_weekly_schedule(goal: str):
    base_schedule = {
        "Monday": ["Work", "Exercise"],
        "Tuesday": ["Study", "Work"],
        "Wednesday": ["Work", "Gym"],
        "Thursday": ["Study", "Rest"],
        "Friday": ["Work", "Gym"],
        "Saturday": ["Personal Project", "Relax"],
        "Sunday": ["Rest", "Planning"]
    }

    if "gym" in goal.lower():
        base_schedule["Monday"].append("Gym")

    return base_schedule