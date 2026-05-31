from agents.model_settings import ModelSettings

HOW_MANY_SEARCHES = 3

TEMPERATURE = 0.7
TOP_P = 1.0
MAX_TOKENS = 4096

PLANNER_MODEL_SETTINGS = ModelSettings(
    temperature=TEMPERATURE,
    top_p=TOP_P,
    max_tokens=1024,
)

SEARCH_MODEL_SETTINGS = ModelSettings(
    temperature=0.3,
    tool_choice="required",
    max_tokens=1024,
)

WRITER_MODEL_SETTINGS = ModelSettings(
    temperature=TEMPERATURE,
    top_p=TOP_P,
    max_tokens=MAX_TOKENS,
)

EMAIL_MODEL_SETTINGS = ModelSettings(
    temperature=0.5,
    max_tokens=4096,
)
