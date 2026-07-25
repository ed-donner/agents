def generate_summary(data: dict):
    parts = []

    if data.get("schedule"):
        parts.append("A structured weekly schedule was created.")

    if data.get("budget"):
        parts.append(f"Total expenses calculated: {data['budget']['total']}.")

    if data.get("priorities"):
        parts.append("Tasks were prioritized based on simplicity.")

    return " ".join(parts)