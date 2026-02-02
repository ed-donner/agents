"""Tool module demonstrating function tools, tool guardrails, and agent composition.

Tools extend agent capabilities beyond text generation, enabling real-world actions
like API calls, database queries, file operations, and delegation to sub-agents.

Tool Execution Flow:
-------------------
```
LLM decides to call tool
        │
        ▼
┌───────────────────────┐
│  Input Guardrails     │──► reject_content() → LLM receives error, can retry
│  (validate arguments) │──► raise_exception() → Execution halts
└───────────────────────┘
        │ allow()
        ▼
┌───────────────────────┐
│  Tool Function        │    Your Python code executes
│  (business logic)     │    (API calls, DB queries, etc.)
└───────────────────────┘
        │
        ▼
┌───────────────────────┐
│  Output Guardrails    │──► reject_content() → LLM receives error
│  (validate result)    │──► raise_exception() → Execution halts
└───────────────────────┘
        │ allow()
        ▼
Result returned to LLM
```

Three Tool Patterns:
-------------------
1. Function Tools: Python functions exposed to LLM via @function_tool decorator
2. Tool Guardrails: Validation layer protecting tool inputs and outputs
3. Agent-as-Tool: Convert agents into callable tools for composition

For other types of tools and detailed docs, see:
https://openai.github.io/openai-agents-python/tools/
"""

import logging
import os
import re
from typing import (
    Dict,
    cast,
)

import requests
from pydantic import (
    BaseModel,
    Field,
)

from agents import (
    Agent,
    FunctionTool,
    Runner,
    ToolGuardrailFunctionOutput,
    ToolInputGuardrail,
    ToolInputGuardrailData,
    ToolOutputGuardrail,
    ToolOutputGuardrailData,
    function_tool,
    tool_input_guardrail,
    tool_output_guardrail,
)


logger = logging.getLogger(__name__)

# =============================================================================
# TOOL GUARDRAILS
# =============================================================================

# Tool guardrails are validation functions that run before or after a tool executes.
# Unlike agent guardrails (which protect agent input/output), tool guardrails protect
# individual tool calls made by the agent.
#
# TWO TYPES OF TOOL GUARDRAILS:
# -----------------------------
# 1. @tool_input_guardrail  - Runs BEFORE the tool executes
#    - Receives: ToolInputGuardrailData (contains tool_arguments, tool context)
#    - Use case: Validate arguments, block dangerous inputs, check permissions
#
# 2. @tool_output_guardrail - Runs AFTER the tool executes
#    - Receives: ToolOutputGuardrailData (contains output + everything from input)
#    - Use case: Validate results, filter sensitive data, ensure quality
#
# THREE RESPONSE BEHAVIORS:
# -------------------------
# - ToolGuardrailFunctionOutput.allow()
#       → Let the tool execute normally (or accept its output)
#
# - ToolGuardrailFunctionOutput.reject_content(message)
#       → Block the tool but continue agent execution with an error message
#       → The LLM receives the message and can try a different approach
#
# - ToolGuardrailFunctionOutput.raise_exception()
#       → Halt execution completely by raising ToolGuardrailTripwireTriggered
#
# KEY DIFFERENCE FROM AGENT GUARDRAILS:
# -------------------------------------
# - Agent guardrails: Protect the overall conversation (user input / final output)
# - Tool guardrails: Protect specific tool calls (arguments / results)
# - Tool guardrails allow graceful recovery via reject_content()
# =============================================================================


class ConfidentialInformation(BaseModel):
    """Structured output model for confidential information detection."""

    is_confidential: bool = Field(..., description="True if confidential information was detected, False otherwise.")
    details: str = Field(
        ..., description="Description of the detected confidential information, or empty if none found."
    )


tool_input_guardrail_agent = Agent(
    name="Confidential Information check",
    instructions="""Check if the response contains any confidential information that should not be shared.
        Confidential information include social security numbers, account numbers, passwords,
        and other sensitive data.
        Names, addresses, and phone numbers are not considered confidential.""",
    output_type=ConfidentialInformation,
    model="gpt-5.2",
)


@tool_input_guardrail
async def reject_confidential_information(data: ToolInputGuardrailData) -> ToolGuardrailFunctionOutput:
    """Input guardrail that blocks tool calls containing confidential information.

    This demonstrates pre-execution validation: inspecting the tool arguments
    before the tool runs.

    The guardrail uses reject_content() to block the call while allowing the
    agent to continue and potentially try a different approach.

    Args:
        data: ToolInputGuardrailData containing:
            - data.context.tool_arguments: JSON string of the tool's arguments
            - data.context.tool_name: Name of the tool being called
            - data.agent: The agent making the tool call

    Returns:
        ToolGuardrailFunctionOutput with either:
            - allow() if input is safe
            - reject_content() if sensitive words are found
            - raise_exception() for excluded patterns
    """
    tool_name = data.context.tool_name
    tool_args = data.context.tool_arguments
    logger.debug("Validating tool input for '%s': %s", tool_name, tool_args)
    result = await Runner.run(tool_input_guardrail_agent, tool_args, context=data.context)
    if result.final_output.is_confidential:
        logger.debug(
            "Tool call to '%s' blocked due to confidential information: %s", tool_name, result.final_output.details
        )
        return ToolGuardrailFunctionOutput.reject_content(
            message="Tool call blocked: contains confidential information.",
            output_info={"confidential_details": result.final_output.details, "tool": tool_name},
        )
    logger.debug("Tool call to '%s' accepted", tool_name)
    return ToolGuardrailFunctionOutput(output_info="Input validated")


EMAIL_REGEX = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")


@tool_output_guardrail
def validate_contains_email(data: ToolOutputGuardrailData) -> ToolGuardrailFunctionOutput:
    """Output guardrail that validates the tool's result contains a valid email.

    This demonstrates post-execution validation: checking that the tool produced
    the expected output format before returning results to the LLM.

    Output guardrails receive ToolOutputGuardrailData which extends input data
    with the actual output from the tool function.

    Args:
        data: ToolOutputGuardrailData containing:
            - data.output: The return value from the tool function
            - data.context: Tool context (same as input guardrail)
            - data.agent: The agent that called the tool

    Returns:
        ToolGuardrailFunctionOutput with either:
            - allow() if output contains valid email
            - reject_content() if validation fails
    """
    tool_name = data.context.tool_name
    tool_output = str(data.output)
    logger.debug("Validating tool output for '%s': %s", tool_name, tool_output)
    if not EMAIL_REGEX.search(tool_output):
        logger.debug("Tool '%s' output validation failed: no valid email found in '%s'", tool_name, tool_output)
        return ToolGuardrailFunctionOutput.reject_content(
            message="The tool output does not contain a valid email address.",
            output_info={"tool_output": tool_output},
        )
    logger.debug("Tool '%s' output validation passed: valid email found in '%s'", tool_name, tool_output)
    return ToolGuardrailFunctionOutput.allow()


# =============================================================================
# FUNCTION TOOLS
# =============================================================================
#
# Function tools allow you to expose Python functions as tools that the LLM can call.
# The @function_tool decorator transforms a regular function into a FunctionTool.
#
# HOW IT WORKS:
# -------------
# 1. The decorator inspects your function's signature (parameters, types, defaults)
# 2. It parses the docstring for descriptions
# 3. It generates a JSON schema that tells the LLM how to call your function
# 4. When the LLM calls the tool, arguments are validated and passed to your function
#
# DECORATOR PARAMETERS:
# ---------------------
# @function_tool(
#     name_override="custom_name",      # Override the function name shown to LLM
#     description_override="...",       # Override docstring description
#     strict_mode=True,                 # Enforce strict JSON schema (recommended)
#     is_enabled=True,                  # Can be bool or callable for dynamic enabling
# )
#
# ATTACHING GUARDRAILS:
# ---------------------
# The @function_tool decorator doesn't support guardrails directly.
# Instead, attach them to the FunctionTool after decoration:
#
#     @function_tool
#     def my_tool(arg: str) -> str: ...
#
#     my_tool.tool_input_guardrails = [input_guardrail_func]
#     my_tool.tool_output_guardrails = [output_guardrail_func]
#
# BEST PRACTICES:
# ---------------
# - Use type hints for all parameters (enables proper JSON schema generation)
# - Write docstrings with Args section (provides parameter descriptions)
# - Keep functions focused on a single task
# - Return serializable types (dict, str, list) that the LLM can understand
# =============================================================================


def push(text: str) -> None:
    """Send a push notification via Pushover API.

    This is a helper function (not a tool) that sends notifications.
    It demonstrates a common pattern: tools often call external services
    to perform real-world actions.

    Note: Requires PUSHOVER_TOKEN and PUSHOVER_USER environment variables.

    Args:
        text: The message text to send as a push notification.
    """
    try:
        requests.post(
            "https://api.pushover.net/1/messages.json",
            data={
                "token": os.getenv("PUSHOVER_TOKEN"),
                "user": os.getenv("PUSHOVER_USER"),
                "message": text,
            },
            timeout=5,
        )
    except Exception as e:
        logger.error("Failed to send push notification: %s", e)


@function_tool(
    description_override="""Use this tool to record that a user is interested in being in touch
        and provided an email address"""
)
def record_user_details(email: str, name: str = "Name not provided", notes: str = "Not provided") -> Dict[str, str]:
    """Record user details for follow-up contact.

    Args:
        email: The email address of this user (required - no default)
        name: The user's name, if they provided it (optional)
        notes: Any additional information about the conversation (optional)

    Returns:
        dict: Confirmation message containing the recorded details.
              Must contain a valid email for the output guardrail to pass.
    """
    tool_output = f"{name} with email {email} and notes {notes}"
    push(f"Recording: {tool_output}")
    return {"recorded": tool_output}


# Attach guardrails to the function tool after decoration.
# The cast() is needed because the decorator returns FunctionTool but the type
# checker sees it as the original function type.
record_user_details.tool_input_guardrails = cast(list[ToolInputGuardrail], [reject_confidential_information])

# =============================================================================
# AGENTS AS TOOLS
# =============================================================================
#
# The OpenAI Agent SDK allows you to convert an Agent into a Tool using as_tool().
# This enables powerful composition patterns where agents can delegate to sub-agents.
#
# KEY CONCEPT: agent.as_tool()
# ----------------------------
# Transforms an agent into a callable tool that other agents can use.
#
#     my_tool = my_agent.as_tool(
#         tool_name="tool_name",           # Must match: ^[a-zA-Z0-9_-]+$ (no spaces!)
#         tool_description="...",          # Helps the LLM know when to use this tool
#     )
#
# HOW IT DIFFERS FROM HANDOFFS:
# -----------------------------
# | Aspect          | as_tool()                    | Handoff                      |
# |-----------------|------------------------------|------------------------------|
# | Input           | Generated by calling agent   | Full conversation history    |
# | Control         | Returns to calling agent     | New agent takes over         |
# | Use case        | Subtask delegation           | Complete task transfer       |
#
# COMPOSITION PATTERNS:
# ---------------------
# 1. SIMPLE: Agent A uses Agent B as a tool
#        Agent A → calls → Agent B (as tool) → returns result → Agent A continues
#
# 2. NESTED: Agent A uses Agent B, which uses Agent C
#        Agent A → Agent B (tool) → Agent C (tool) → result bubbles up
#
# 3. MULTI-TOOL: Agent uses multiple agent-tools
#        Agent A → can call → Agent B (tool) OR Agent C (tool) OR function_tool
#
# GUARDRAILS ON AGENT-TOOLS:
# --------------------------
# Agent-tools return FunctionTool, so you can attach guardrails:
#     agent_tool = cast(FunctionTool, my_agent.as_tool(...))
#     agent_tool.tool_output_guardrails = [my_guardrail]
# =============================================================================


class ContactRequest(BaseModel):
    """Pydantic model for structured contact information extraction.

    When used as an Agent's output_type, the agent is forced to return
    data matching this schema. This enables:
    - Type-safe structured outputs
    - Automatic validation
    - Clear contract between agents

    The LLM will extract and format user input to match these fields.
    """

    name: str
    email: str
    notes: str


# -----------------------------------------------------------------------------
# EXAMPLE: Simple Agent-as-Tool
# -----------------------------------------------------------------------------
# This agent extracts contact info and returns structured data.
# It's converted to a tool so other agents can use it for extraction.

contact_info_agent = Agent(
    name="Contact Info Extractor Agent",
    instructions="""Extract contact information from user messages.
    Parse the user's message to identify their name, email, and any notes.
    Return structured data matching the ContactRequest schema.""",
    output_type=ContactRequest,  # Forces structured output
    model="gpt-5.2",
)

# Convert agent to tool - note the cast() for type checking
contact_info_tool = cast(
    FunctionTool,
    contact_info_agent.as_tool(
        tool_name="contact_info_extractor",
        tool_description="Extracts contact information (name, email, notes) from user messages.",
    ),
)

# Attach output guardrail to validate the extracted email
contact_info_tool.tool_output_guardrails = cast(list[ToolOutputGuardrail], [validate_contains_email])


# -----------------------------------------------------------------------------
# EXAMPLE: Nested Agent as a Tool with Multi-Tool Composition
# -----------------------------------------------------------------------------
# This agent orchestrates the workflow by using:
# - contact_info_tool (agent-as-tool): To extract contact info
# - record_user_details (function-tool): To save the extracted info
#
# This demonstrates how agent tools can compose both agent-tools and function-tools.

send_contact_request_agent = Agent(
    name="Send Contact Request Agent",
    instructions="""Handle user contact requests by:
    1. Using the contact_info_extractor tool to parse the user's message
    2. Using the record_user_details tool to save the extracted information

    Coordinate these tools to complete the contact request workflow.""",
    model="gpt-5.2",
    tools=[contact_info_tool, record_user_details],  # Mix of agent-tool and function-tool
)

send_contact_request_tool = send_contact_request_agent.as_tool(
    tool_name="send_contact_request",
    tool_description="""Complete workflow:
        extracts contact info and records it. Use for handling user contact requests.""",
)
