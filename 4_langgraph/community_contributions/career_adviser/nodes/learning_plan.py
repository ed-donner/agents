def learning_plan_node(state):
    gaps = state["skill_gaps"]

    all_gaps = set()
    for g in gaps.values():
        all_gaps.update(g)

    if not all_gaps:
        state["learning_plan"] = "No major gaps. You're ready!"
    else:
        plan = "Learning Plan:\n"
        for skill in all_gaps:
            plan += f"- Learn {skill}\n"

        state["learning_plan"] = plan

    return state