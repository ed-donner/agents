def clarifier_node(state):
    state["user_input"]["goal"] = "AI Engineer"
    state["clarified"] = True
    return state