from typing import TypedDict, List, Dict

class CareerState(TypedDict):
    user_input: dict
    clarified: bool
    roles: List[str]
    skill_gaps: Dict[str, List[str]]
    learning_plan: str
    final_report: str
    next_step: str