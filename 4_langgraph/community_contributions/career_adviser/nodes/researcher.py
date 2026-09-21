from data.roles import ROLE_SKILLS

def research_node(state):
    goal = state["user_input"]["goal"]

    roles = [role for role in ROLE_SKILLS if goal.lower() in role.lower()]

    if not roles:
        roles = ["Software Engineer"]

    state["roles"] = roles
    return state