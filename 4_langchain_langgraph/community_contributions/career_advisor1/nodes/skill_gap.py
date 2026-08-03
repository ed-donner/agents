from data.roles import ROLE_SKILLS

def skill_gap_node(state):
    user_skills = state["user_input"].get("skills", [])
    gaps = {}

    for role in state["roles"]:
        required = ROLE_SKILLS.get(role, [])
        missing = list(set(required) - set(user_skills))
        gaps[role] = missing

    state["skill_gaps"] = gaps
    return state