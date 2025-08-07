from agents import (
    Agent,
    GuardrailFunctionOutput,
    ModelSettings,
    OpenAIChatCompletionsModel,
    Runner,
    RunResult,
    TResponseInputItem,
    WebSearchTool,
    input_guardrail,
)

# from dotenv import load_dotenv
from llm_models import llm_manager
from schemas import EvaluationFeedback

# print(f"INFO | Loading .env file success: {load_dotenv(override=True)}")
# GOOGLE_SEARCH_API_KEY: str | None = os.environ.get("GOOGLE_SEARCH_API_KEY")
# GOOGLE_SEARCH_CONTEXT: str | None = os.environ.get("GOOGLE_SEARCH_CONTEXT")


available_model: OpenAIChatCompletionsModel | None = llm_manager.get_model(
    provider="groq"
)

# deepseek_model: OpenAIChatCompletionsModel | None = llm_manager.get_model("deepseek")
# groq_model: OpenAIChatCompletionsModel | None = llm_manager.get_model("groq")

# print(f"INFO | {available_model.__dir__()}")
# print(f"INFO | Available Model Names: {available_model.model}")


##############################
# Agent 1 - Exercise Generator
##############################
exercise_generator: Agent = Agent(
    name="story_outline_generator",
    instructions=(
        "You generate a coding exercise based on the user's topic of interest.If there is any feedback provided, use it to improve the exercise."
    ),
    model=available_model,
)

#####################
# Agent 2 - Evaluator
#####################
evaluator: Agent = Agent[None](
    name="evaluator",
    instructions=(
        "You evaluate the exercise and decide if it's good enough. If it's not good enough, you provide feedback on what needs to be improved. Never give it a pass on the first try."
    ),
    output_type=EvaluationFeedback,
    model=available_model,
)
