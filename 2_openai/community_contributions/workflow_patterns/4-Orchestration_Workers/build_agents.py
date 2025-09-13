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
from schemas import SyllabusData, TopicCheckOutput, WebSearchPlan

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

MAX_TOKENS = 3000

#########################
# Agent 1 - Planner Agent
#########################
HOW_MANY_SEARCHES = 2
planner_agent: Agent = Agent(
    name="PlannerAgent",
    instructions=(
        f"You are a programming syllabus creator agent. Given a programming topic, propose 5-20 web searches that, together, will answer it comprehensively. Output strictly {HOW_MANY_SEARCHES} terms to query for. Return them as JSON in the schema provided."
    ),
    model=available_model,
    output_type=WebSearchPlan,
    # input_guardrails=[check_if_on_topic]
    model_settings=ModelSettings(
        max_tokens=MAX_TOKENS,
    ),
)

########################
# Agent 2 - Search Agent
########################
search_agent: Agent = Agent(
    name="SearchAgent",
    instructions=(
        "You are an internet researcher. Use the WebSearch tool to gather the most relevant information for the given query. Summarize your findings in clear, markdown bullets (≤300 words)."
    ),
    tools=[WebSearchTool()],
    # force the model to choose the tool; no stray text-only answers
    model_settings=ModelSettings(tool_choice="required", max_tokens=MAX_TOKENS),
)

########################
# Agent 3 - Writer Agent
########################
writer_agent: Agent = Agent(
    name="WriterAgent",
    instructions=(
        "You are a senior technical syllabus writer agent. Combine the provided research summaries into a concise, well-structured report (approx. 500-1000 words of markdown). Begin with a one-paragraph outline of the syllabus, then the full syllabus."
    ),
    model=available_model,
    output_type=SyllabusData,
    model_settings=ModelSettings(max_tokens=MAX_TOKENS),
)

######################################################
# This is the Guardrail agent that performs the check.
######################################################
guardrail_topic_checker_agent: Agent = Agent(
    name="TopicChecker",
    instructions="You are a topic checker for a programming syllabus. Your job is to determine if the user's question is about Python, JavaScript, or SQL. If it is not, you must create a helpful message explaining that you can only answer questions on those topics.",
    output_type=TopicCheckOutput,  # Tell the agent to use our Pydantic model
    model=available_model,
    model_settings=ModelSettings(max_tokens=MAX_TOKENS),
)


@input_guardrail
async def check_if_on_topic(
    ctx,
    agent: Agent,
    message: list[TResponseInputItem],
) -> GuardrailFunctionOutput:
    """
    This guardrail function runs the specialized guardrail (TopicChecker) agent
    to see if the user's message is on topic. It expects a list of messages and checks the last one.
    """
    print("\nINFO | Guardrail | Checking if the message is on topic...")

    # Extract the content of the last message from the list.
    # The guardrail checker agent expects a simple string.
    last_user_message: str = (
        message[-1]["content"] if message and message[-1]["role"] == "user" else ""
    )

    if not last_user_message:
        # If there's no message, no need to stop.
        return GuardrailFunctionOutput(tripwire_triggered=False)

    # print(f"\nINFO | Guardrail | Last user message: {last_user_message}")

    # Run the specialized guardrail agent on the user's message content
    result: RunResult = await Runner.run(
        starting_agent=guardrail_topic_checker_agent,
        input=last_user_message,  # Pass the extracted string here
        # context={"message_history": message},  # Full history for context
        context=ctx.context,
    )

    # Assert that the output is the type we expect
    assert isinstance(result.final_output, TopicCheckOutput)

    # Decide if the "tripwire" was triggered.
    should_stop: bool = not result.final_output.is_on_topic

    return GuardrailFunctionOutput(
        output_info={"Found_Unexpected_Message": result.final_output},
        tripwire_triggered=should_stop,
    )


# Guardrail agent that uses the guardrail | This agent will route the user to the appropriate specialist based on their question.
routing_agent: Agent = Agent(
    name="RoutingAgent",
    instructions="You're a smart routing agent. Based on the user's message, you check whether the input is on the topic related to Syllabus generation for Python, JavaScript, or SQL. If topic is about Python, JavaScript, or SQL, route to the PlannerAgent",
    model=available_model,
    handoffs=[planner_agent],
    input_guardrails=[check_if_on_topic],  # Guardrail function
    model_settings=ModelSettings(max_tokens=MAX_TOKENS),
)
