def manager_node(state):
    user = state["user_input"]

    if not user.get("goal"):
        state["next_step"] = "clarifier"
    else:
        state["next_step"] = "research"

    return state