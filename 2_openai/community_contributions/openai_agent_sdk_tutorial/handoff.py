"""
Handoff Module - Agent-to-Agent Control Transfer

This module demonstrates the OpenAI Agent SDK's handoff mechanism, which allows
one agent to transfer control of the conversation to another specialized agent.

Key Concepts
------------
Handoffs vs Agents-as-Tools:
Both patterns enable multi-agent architectures, but they differ fundamentally:
+------------------+----------------------------------+----------------------------------+
| Aspect           | Handoff                          | Agent-as-Tool                    |
+==================+==================================+==================================+
| Control Flow     | Target agent takes over          | Caller retains control           |
|                  | completely                       |                                  |
+------------------+----------------------------------+----------------------------------+
| Conversation     | Full history passed to           | Only tool input/output           |
| Context          | target agent                     | exchanged                        |
+------------------+----------------------------------+----------------------------------+
| Return Behavior  | Target agent responds            | Result returned to caller        |
|                  | directly to user                 | for processing                   |
+------------------+----------------------------------+----------------------------------+
| Use Case         | Escalation, specialization,      | Subtasks, delegation,            |
|                  | routing                          | composition                      |
+------------------+----------------------------------+----------------------------------+

When to Use Handoffs:
- User requests to speak with a different department or supervisor
- The current agent cannot handle a specific domain (e.g., billing → technical support)
- Escalation scenarios requiring different permissions or capabilities
- Language routing (e.g., transfer to Spanish-speaking agent)

Handoff Components:
1. Target Agent: The agent that will receive control
2. on_handoff callback: Optional function called when handoff occurs
3. input_type: Optional Pydantic model for structured handoff data
4. input_filter: Optional Function to modify conversation history before transfer

For more details, see:
https://openai.github.io/openai-agents-python/handoffs/
"""

import logging

from pydantic import (
    BaseModel,
    Field,
)

from agents import (
    Agent,
    HandoffInputData,
    RunContextWrapper,
    handoff,
)

from .hook import MyAgentHook
from .tool import send_contact_request_tool


logger = logging.getLogger(__name__)


# =============================================================================
# HANDOFF DATA MODEL
# =============================================================================
# When using input_type with handoff(), the SDK expects structured data from
# the LLM when it decides to perform a handoff. This data is validated against
# the Pydantic model and passed to the on_handoff callback.


class EscalationData(BaseModel):
    """Structured data model for escalation handoffs.

    This model defines the information collected when the main agent
    decides to escalate a conversation to a supervisor. The LLM will
    populate these fields based on the conversation context.
    """

    reason: str = Field(..., description="A description of why the escalation is occurring.")


# =============================================================================
# HANDOFF CALLBACK
# =============================================================================
# The on_handoff callback is invoked when a handoff occurs. It receives:
# - context: The RunContextWrapper with custom context data
# - input_data: The structured data (matching input_type) from the LLM
#
# Use cases for on_handoff:
# - Logging/auditing handoff events
# - Sending notifications to supervisors
# - Updating metrics or dashboards
# - Performing pre-handoff validation


async def on_escalation(context: RunContextWrapper, input_data: EscalationData) -> None:
    """Callback executed when an escalation handoff occurs.

    This function is called after the LLM decides to perform a handoff
    but before control is transferred to the target agent. It provides
    an opportunity to log, notify, or perform side effects.

    Args:
        context: RunContextWrapper containing the shared context from
                 Runner.run(context=...). Access custom data via context.context.
        input_data: The structured escalation data populated by the LLM,
                    validated against the EscalationData model.
    """
    logger.debug("Handoff executed. Context: %s", context.context)
    # In production, this might:
    # - Send a Slack notification to supervisors
    # - Create a ticket in a support system
    # - Log to an audit trail
    print(f"Escalation agent called with reason: {input_data.reason}")


# =============================================================================
# INPUT FILTER
# =============================================================================
# The input_filter function allows you to modify the conversation history
# before it's passed to the target agent. This is useful for:
#
# - Removing sensitive information from history
# - Filtering out irrelevant tool calls
# - Summarizing long conversations
# - Removing duplicate messages
#
# The filter receives HandoffInputData and must return HandoffInputData.
# Modifying input_items affects what the target agent sees, while new_items
# is preserved for session history.


def handoff_input_filter(handoff_input_data: HandoffInputData) -> HandoffInputData:
    """Filter and transform conversation history before handoff.

    This function is called before the target agent receives the conversation.
    It can modify what history the new agent sees while preserving the full
    history for session records.

    Args:
        handoff_input_data: Contains all conversation history components:
            - input_history: Input history before `Runner.run()` was called
            - pre_handoff_items: Items generated before the agent turn where the handoff was invoked
            - new_items: New items generated during the current agent turn, including the item that
                    triggered the handoff
            - input_items: Items to include in the next agent's input. When set, these items are used
                    instead of new_items for building the input to the next agent.
            - run_context: Current execution context

    Returns:
        HandoffInputData: Modified handoff data. The input_items field
        determines what the target agent receives.
    """
    input_history = handoff_input_data.input_history
    pre_handoff_items = handoff_input_data.pre_handoff_items
    new_items = handoff_input_data.new_items
    input_items = handoff_input_data.input_items

    # Currently passing through unchanged - customize as needed
    filtered_input_history = input_history
    filtered_pre_handoff_items = pre_handoff_items
    filtered_new_items = new_items
    filtered_input_items = input_items

    return HandoffInputData(
        input_history=filtered_input_history,
        pre_handoff_items=filtered_pre_handoff_items,
        new_items=filtered_new_items,
        input_items=filtered_input_items,
        run_context=handoff_input_data.run_context,
    )


# =============================================================================
# TARGET AGENT
# =============================================================================
# The escalation agent is the target of the handoff. When the main agent
# invokes the handoff, this agent takes over the conversation completely.
#
# Key configuration:
# - handoff_description: Helps the calling agent decide when to handoff
# - The target agent can have its own tools, guardrails, and hooks
# - The target agent sees the (potentially filtered) conversation history

escalation_agent = Agent(
    name="Rude Escalation Agent",
    instructions="""
You are a rude financial services supervisor that handles escalated requests from a notification agent.
Your responsibilities:
- Help users to record their requests
- Send push notifications when appropriate
Guidelines:
- Be concise and unfriendly in your responses
- Only send notifications for important or requested information
- Do not engage in small talk or pleasantries
- Always replay in Spanish
""",
    model="gpt-5.2",
    tools=[send_contact_request_tool],
    # handoff_description helps the CALLING agent decide when to use this handoff.
    # It's shown to the LLM as part of the tool description.
    handoff_description="Escalate the request if the user asks you to talk to a supervisor",
    hooks=MyAgentHook(),
)


# =============================================================================
# HANDOFF DEFINITION
# =============================================================================
# The handoff() function creates a tool that the calling agent can invoke
# to transfer control. Configuration options:
#
# - agent: The target agent to hand off to (required)
# - on_handoff: Callback when handoff occurs (optional)
# - tool_name_override: Custom tool name (default: "transfer_to_{agent.name}")
# - tool_description_override: Custom description for the calling agent
# - input_type: Pydantic model for structured handoff data (optional)
# - input_filter: Function to modify history before transfer (optional)

supervisor_escalation = handoff(
    agent=escalation_agent,
    on_handoff=on_escalation,
    tool_name_override="supervisor_handoff_tool",
    tool_description_override="Tool for escalating requests to a supervisor",
    input_type=EscalationData,
    input_filter=handoff_input_filter,
)
