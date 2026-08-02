def final_report_node(state):
    report = "=== Career Advice Report ===\n\n"

    report += "Recommended Roles:\n"
    for role in state["roles"]:
        report += f"- {role}\n"

    report += "\nSkill Gaps:\n"
    for role, gaps in state["skill_gaps"].items():
        report += f"{role}: {', '.join(gaps) if gaps else 'None'}\n"

    report += "\n" + state["learning_plan"]

    state["final_report"] = report
    return state