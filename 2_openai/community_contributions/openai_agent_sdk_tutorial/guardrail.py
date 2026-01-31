"""Guardrail module demonstrating agent-level input and output validation.

This module showcases Agent Guardrails - a safety mechanism that validates
user input and agent output at the Agent level.

Key Concepts:
------------
1. Agent Guardrails vs Tool Guardrails: This module demonstrates Agent Guardrails
   which validate the overall conversation flow. Tool Guardrails (in tool.py) validate
   individual tool calls.

2. Guardrail Agents: Using a separate agent to perform validation is a powerful
   pattern that leverages LLM reasoning for complex content moderation.

Agent Guardrail Types:
---------------------
- @input_guardrail: Validates user input BEFORE the main agent processes it
- @output_guardrail: Validates agent output BEFORE returning to the user

Guardrail Behavior:
------------------
Unlike Tool Guardrails which can gracefully reject content, Agent Guardrails
ALWAYS raise exceptions when triggered:

- Input guardrail triggers → raises `InputGuardrailTripwireTriggered`
- Output guardrail triggers → raises `OutputGuardrailTripwireTriggered`

This means Agent Guardrails are "hard stops" - there's no way for the agent
to recover or retry. Use them for content that should never be processed.

When to Use Agent Guardrails:
----------------------------
- Content moderation (hate speech, harassment, illegal content)
- PII detection and blocking
- Prompt injection detection
- Compliance requirements (regulatory, legal)
- Brand safety enforcement

Architecture:
------------
```
User Input
    │
    ▼
┌─────────────────────────┐
│   Input Guardrail       │ ◄── Raises InputGuardrailTripwireTriggered if triggered
│   (validates input)     │
└─────────────────────────┘
    │ (if passes)
    ▼
┌─────────────────────────┐
│   Main Agent            │
│   (processes request)   │
└─────────────────────────┘
    │
    ▼
┌─────────────────────────┐
│   Output Guardrail      │ ◄── Raises OutputGuardrailTripwireTriggered if triggered
│   (validates output)    │
└─────────────────────────┘
    │ (if passes)
    ▼
Response to User
```

Comparison: Agent Guardrails vs Tool Guardrails:
------------------------------------------------------------------------------
| Aspect              | Agent Guardrails          | Tool Guardrails           |
|---------------------|---------------------------|---------------------------|
| Scope               | Entire conversation       | Single tool call          |
| Trigger behavior    | Always raises exception   | Can recover gracefully    |
| Use case            | Hard content policy       | Validate tool args/output |
| Decorator           | @input_guardrail          | @tool_input_guardrail     |
|                     | @output_guardrail         | @tool_output_guardrail    |
| Recovery options    | None (must catch in app)  | reject_content(), allow() |
|---------------------|---------------------------|---------------------------|

For more detaill see:
https://openai.github.io/openai-agents-python/guardrails/
"""

import logging
from typing import (
    Any,
    List,
    Union,
)

from pydantic import BaseModel

from agents import (
    Agent,
    GuardrailFunctionOutput,
    RunContextWrapper,
    Runner,
    TResponseInputItem,
    input_guardrail,
    output_guardrail,
)


logger = logging.getLogger(__name__)


# =============================================================================
# STRUCTURED OUTPUT FOR GUARDRAIL
# =============================================================================
#
#   Using Pydantic models for guardrail output provides:
#   1. Type safety: Guaranteed structure for downstream processing
#   2. Validation: Automatic validation of LLM responses
#   3. Documentation: Self-documenting schema for the expected output

# The output_type parameter on Agent forces the LLM to return JSON
# matching this schema, which is then parsed into this Pydantic model.


class FoulLanguage(BaseModel):
    """Structured output model for foul language detection.

    Attributes:
        is_foul_language: True if foul language was detected, False otherwise.
        offense: Description of the detected offense, or empty if none found.
    """

    is_foul_language: bool
    offense: str


class UnprofessionalResponse(BaseModel):
    """Structured output model for unprofessional response detection.

    Attributes:
        is_not_professional: True if the response was unprofessional, False otherwise.
        reasoning: Explanation of why the response was classified as unprofessional, or empty if none found.
    """

    is_not_professional: bool
    reasoning: str


# =============================================================================
# GUARDRAIL AGENT
# =============================================================================

# Pattern: Using an Agent as a Guardrail Validator
# ------------------------------------------------
# This is a powerful pattern where we use a separate LLM agent to perform
# content validation.
#
# Benefits:
# 1. Nuanced Understanding: LLMs can detect subtle policy violations that
#    rule-based systems miss (sarcasm, context-dependent offense, etc.)
# 2. Explainability: The agent can explain WHY content was flagged
# 3. Adaptability: Easy to adjust detection by changing instructions
# 4. Consistency: Single model for both main agent and guardrail ensures
#    consistent interpretation of content policies
#
# Trade-offs:
# - Additional latency (extra LLM call)
# - Additional cost (more tokens processed)
# - Potential for false positives/negatives
#
# For production, consider:
# - Caching results for repeated content
# - Using faster/cheaper models for guardrails
# - Combining with rule-based pre-filters

input_guardrail_agent = Agent(
    name="Foul language checker",
    instructions="""You are a input checker agent.
    Your task is to evaluate that the users of other agents are not using foul language.
    For each input, provide:
    1. A classification of the response as foul language or not.
    2. The words that are considered foul language.""",
    output_type=FoulLanguage,
    model="gpt-5.2",
)

output_guardrail_agent = Agent(
    name="Professional response checker",
    instructions="""You are a response checker agent.
    Your task is to evaluate the professionalism of the output generated by other agents in
    a financial services customer support environment.
    Off topic answers (non financial services related), informal, rude or inappropriate language
    are considered unprofessional.
    For each response, provide:
    1. A classification of the response as unprofessional or not.
    2. A brief explanation of the reasoning behind the classification.""",
    output_type=UnprofessionalResponse,
    model="gpt-5.2",
)


# =============================================================================
# INPUT GUARDRAIL
# =============================================================================

#     Input Guardrail Execution:
#     -------------------------
#     The guardrail function is called automatically by the SDK:
#     1. User sends a message
#     2. Input guardrails run BEFORE the main agent sees the input
#     3. If tripwire_triggered=True, raises InputGuardrailTripwireTriggered
#     4. If tripwire_triggered=False, main agent proceeds normally

#     Function Signature Requirements:
#     -------------------------------
#     Input guardrails MUST follow this exact signature:
#     - context: RunContextWrapper - Access to custom context data
#     - agent: Agent - The agent this guardrail is attached to (NOT the guardrail agent)
#     - input: Union[str, List[TResponseInputItem]] - The user's input to validate

#     The function MUST return GuardrailFunctionOutput with:
#     - output_info: Dict with any metadata (accessible in exception handler)
#     - tripwire_triggered: bool - True to block, False to allow

#     Context Propagation:
#     -------------------
#     Notice how we pass context.context to the guardrail agent's Runner.run().
#     This ensures the guardrail has access to the same custom context data
#     as the main agent (user info, preferences, etc.).


@input_guardrail
async def input_guardrail_foul_language(
    context: RunContextWrapper, agent: Agent, input: Union[str, List[TResponseInputItem]]
) -> GuardrailFunctionOutput:
    """Validate user input for foul language before agent processing.

    Args:
        context: RunContextWrapper containing custom context from Runner.run(context=...).
                 Access via context.context.
        agent: The Agent instance this guardrail is attached to. Useful for
               accessing agent configuration or name for logging.
        input: The user's input - either a string or a list of message items
               (for multi-turn conversations or complex inputs).

    Returns:
        GuardrailFunctionOutput with:
        - output_info: Metadata about the validation (stored in exception if triggered)
        - tripwire_triggered: True if foul language detected, False otherwise

    Raises:
        InputGuardrailTripwireTriggered: Raised by the SDK if tripwire_triggered=True.
                                         Catch this in your application code.
    """
    logger.debug("Running Input Guardrail:")
    logger.debug("Context: %s", context.context)
    logger.debug("Agent's Name: %s", agent.name)
    logger.debug("Input: %s", input)

    if isinstance(input, str):
        message = input
    elif isinstance(input, list) and len(input) > 0:
        message = str(input[-1])
    else:
        logger.error("Running Input Guardrail: Invalid input type or empty list")
        return GuardrailFunctionOutput(
            output_info={"found_foul_language": None},
            tripwire_triggered=False,
        )
    result = await Runner.run(input_guardrail_agent, message, context=context.context)
    return GuardrailFunctionOutput(
        output_info={"found_foul_language": result.final_output.offense},
        tripwire_triggered=result.final_output.is_foul_language,
    )


# =============================================================================
# OUTPUT GUARDRAIL
# =============================================================================

#     Output Guardrail Execution:
#     --------------------------
#     The guardrail function called automatically by the SDK:
#     1. Main agent generates a text response (not tool calls)
#     2. Output guardrails run BEFORE the response is returned
#     3. If tripwire_triggered=True, raises OutputGuardrailTripwireTriggered
#     4. If tripwire_triggered=False, response is returned to the caller

#   Function Signature Requirements:
#   -------------------------------
#   Output guardrails MUST follow this exact signature:
#   - context: RunContextWrapper - Access to custom context data
#   - agent: Agent - The agent that generated this output
#   - output: Any - The agent's output to validate (usually a string)


@output_guardrail
async def output_guardrail_unprofessional(
    context: RunContextWrapper, agent: Agent, output: Any
) -> GuardrailFunctionOutput:
    """Validate agent output for confidential information before returning to user.

    Args:
        context: RunContextWrapper containing custom context from Runner.run(context=...).
        agent: The Agent instance that generated this output.
        output: The agent's response to validate. Type depends on agent configuration.

    Returns:
        GuardrailFunctionOutput with:
        - output_info: Metadata about the validation (stored in exception if triggered)
        - tripwire_triggered: True if foul language detected, False otherwise

    Raises:
        OutputGuardrailTripwireTriggered: Raised by the SDK if tripwire_triggered=True.
                                          Catch this in your application code.
    """
    logger.debug("Running Output Guardrail:")
    logger.debug("Context: %s", context.context)
    logger.debug("Agent's Name: %s", agent.name)
    logger.debug("Output: %s", str(output))

    result = await Runner.run(output_guardrail_agent, output, context=context.context)
    return GuardrailFunctionOutput(
        output_info={"found_unprofessional": result.final_output.reasoning},
        tripwire_triggered=result.final_output.is_not_professional,
    )
