import os
from dotenv import load_dotenv

load_dotenv(override=True)

# Environment variable names for each agent role
ENG_LEAD = "ENG_LEAD_MODEL"
BACKEND = "BACKEND_ENGINEER_MODEL"
FRONTEND = "FRONTEND_ENGINEER_MODEL"
TESTER = "TEST_ENGINEER_MODEL"

# Maps agent role (as named in agents.yaml / crew.py) → env var name
ROLE_ENV_MAP = {
    "engineering_lead": ENG_LEAD,
    "backend_engineer": BACKEND,
    "frontend_engineer": FRONTEND,
    "test_engineer": TESTER,
}


def get_model_string_for_role(role: str) -> str:
    """Get model string (e.g. 'groq/llama-3.3-70b-versatile') for an agent role."""
    env_var = ROLE_ENV_MAP.get(role)
    if not env_var:
        raise ValueError(f"Unknown role: {role}. Valid: {list(ROLE_ENV_MAP.keys())}")
    value = os.getenv(env_var)
    if not value:
        raise ValueError(
            f"Missing env var {env_var} for role '{role}'. "
            f"Set it in .env or check .env.example"
        )
    return value


def get_all_agent_models() -> dict:
    """Return mapping of role → model string for all agents."""
    return {role: get_model_string_for_role(role) for role in ROLE_ENV_MAP}
