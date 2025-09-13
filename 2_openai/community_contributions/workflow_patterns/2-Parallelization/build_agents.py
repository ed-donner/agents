from agents import Agent, OpenAIChatCompletionsModel
from llm_models import llm_manager

gemini_model: OpenAIChatCompletionsModel | None = llm_manager.get_model(
    provider="gemini"
)
# deepseek_model: OpenAIChatCompletionsModel | None = llm_manager.get_model("deepseek")
# groq_model: OpenAIChatCompletionsModel | None = llm_manager.get_model("groq")

groq_model: OpenAIChatCompletionsModel | None = llm_manager.get_model(
    provider="groq2"  # Updated model provider
)

# print(f"INFO | {groq_model.__dir__()}")
# print(f"INFO | Available Model Names: {groq_model.model}, {groq_model.model}")

# Agent that gives Python explanations
ag_coding_explainer: Agent = Agent(
    name="coding_explainer",
    instructions="You are a coding tutor. You explain the given programming concept snippet in simple terms for a beginner learning to code.",
    model=groq_model,
)

# Agent that selects the best explanation
ag_explanation_picker: Agent = Agent(
    name="explanation_picker",
    instructions="You choose the most beginner-friendly and technically correct explanation from the provided options.",
    model=gemini_model,
    # output_type=OutputQualityCheck,
)
