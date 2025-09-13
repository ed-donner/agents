from agents import (
    Agent,
    GuardrailFunctionOutput,
    OpenAIChatCompletionsModel,
    Runner,
    RunResult,
    TResponseInputItem,
    input_guardrail,
)
from llm_models import llm_manager
from schemas import TopicCheckOutput

available_model: OpenAIChatCompletionsModel | None = llm_manager.get_model(
    provider="groq"
)
# deepseek_model: OpenAIChatCompletionsModel | None = llm_manager.get_model("deepseek")
# groq_model: OpenAIChatCompletionsModel | None = llm_manager.get_model("groq")

# print(f"INFO | {available_model.__dir__()}")
# print(f"INFO | Available Model Names: {available_model.model}")

ag_python_tutor: Agent = Agent(
    name="python_tutor",
    instructions="You're a Python expert. Help the user understand or debug Python code.",
    model=available_model,
)

ag_js_tutor: Agent = Agent(
    name="js_tutor",
    instructions="You're a JavaScript expert. Help the user with JS questions or problems.",
    model=available_model,
)

ag_sql_tutor: Agent = Agent(
    name="sql_tutor",
    instructions="You're an SQL expert. Help the user write or optimize SQL queries.",
    model=available_model,
)

# This is the agent that performs the check.
guardrail_topic_checker_agent: Agent = Agent(
    name="TopicChecker",
    instructions="You are a topic checker for a programming tutor. Your job is to determine if the user's question is about Python, JavaScript, or SQL. If it is not, you must create a helpful message explaining that you can only answer questions on those topics.",
    output_type=TopicCheckOutput,  # Tell the agent to use our Pydantic model
    model=available_model,
)


@input_guardrail
async def check_if_on_topic(
    ctx,
    agent: Agent,
    message: list[TResponseInputItem],
) -> GuardrailFunctionOutput:
    """
    This guardrail function runs the specialized guardrail (TopicChecker) agent
    to see if the user's message is on topic.
    It expects a list of messages and checks the last one.
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


# Routing agent that uses the guardrail | This agent will route the user to the appropriate specialist based on their question.
routing_agent: Agent = Agent(
    name="triage_agent",
    instructions="You're a smart tutor coordinator. Based on the user's message, route them to the correct specialist (Python, JavaScript, or SQL).",
    model=available_model,
    handoffs=[ag_python_tutor, ag_js_tutor, ag_sql_tutor],
    input_guardrails=[check_if_on_topic],  # Guardrail function
)
