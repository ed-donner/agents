from crewai import LLM

from .config import get_model_string_for_role


def create_llm(role: str) -> LLM:
    """Create a CrewAI LLM for a given agent role.

    Args:
        role: Agent role key like "engineering_lead", "backend_engineer",
              "frontend_engineer", or "test_engineer".

    Returns:
        A CrewAI LLM instance configured to use the model specified for that role.
    """
    model_string = get_model_string_for_role(role)
    return LLM(model=model_string)
