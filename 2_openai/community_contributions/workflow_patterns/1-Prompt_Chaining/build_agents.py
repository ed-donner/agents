from agents import Agent, OpenAIChatCompletionsModel
from configs import CurriculumCheckOutput
from llm_models import llm_manager

# print(f"INFO | Current working directory: {os.getcwd()}")
# print(f"INFO | Loading .env file success: {load_dotenv(override=True)}")
# print(f"INFO | {CurriculumCheckOutput}")
# print(f"INFO | Available LLMs: {llm_manager._registry.keys()}")

# gemini_model: OpenAIChatCompletionsModel | None = llm_manager.get_model(
#     provider="gemini"
# )
# deepseek_model: OpenAIChatCompletionsModel | None = llm_manager.get_model("deepseek")
# groq_model: OpenAIChatCompletionsModel | None = llm_manager.get_model("groq")

model_provider = "groq"  # Updated model provider
available_model: OpenAIChatCompletionsModel | None = llm_manager.get_model(
    provider=model_provider
)

# print(f"INFO | {gemini_model.__dir__()}")
print(f"INFO | Available Model Name: {available_model.model}")

# Agent 1: Generate Learning Plan
curriculum_agent: Agent = Agent(
    name="curriculum_agent",
    instructions="Generate a structured curriculum outline to help someone achieve the programming learning goal they provide.",
    model=available_model,
)

# Agent 2: Evaluate learning plan
curriculum_checker_agent: Agent = Agent(
    name="curriculum_checker_agent",
    instructions="Evaluate the provided curriculum outline. Determine if it is high quality and if it matches the user’s learning goal.",
    output_type=CurriculumCheckOutput,
    model=available_model,
)

# Agent 3: Generate full lessons for each section
lesson_writer_agent: Agent = Agent(
    name="lesson_writer_agent",
    instructions="Write a detailed coding lesson for each section in the curriculum outline. Include explanations, code examples, and one practice question per section.",
    output_type=str,
    model=available_model,
)
