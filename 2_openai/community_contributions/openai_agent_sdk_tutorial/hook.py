"""Hooks module demonstrating lifecycle callbacks for agent execution.

Hooks provide visibility into the internal execution of agents, enabling
logging, metrics, debugging, and custom behavior injection.

Execution Timeline with Hooks:
-----------------------------
```
Runner.run() starts
    │
    ├─► on_agent_start(agent)          ◄── Agent begins processing
    │       │
    │       ├─► on_llm_start(...)      ◄── Before LLM API call
    │       │       │
    │       │       ▼
    │       │   [LLM generates response]
    │       │       │
    │       ├─► on_llm_end(response)   ◄── After LLM returns
    │       │
    │       │   (if LLM called a tool)
    │       ├─► on_tool_start(tool)    ◄── Before tool executes
    │       │       │
    │       │       ▼
    │       │   [Tool function runs]
    │       │       │
    │       ├─► on_tool_end(result)    ◄── After tool returns
    │       │       │
    │       │       ▼
    │       │   [Loop: back to on_llm_start if more work needed]
    │       │
    │       │   (if agent hands off)
    │       ├─► on_handoff(from, to)   ◄── Control transfers
    │       │
    ├─► on_agent_end(output)           ◄── Agent finishes
    │
    ▼
Runner.run() returns
```

Common Use Cases:
----------------
- Logging: Debug agent behavior by logging each lifecycle event
- Metrics: Track LLM latency, tool usage frequency, handoff patterns
- Cost tracking: Monitor token usage via on_llm_end response metadata
- Audit trails: Record all agent actions for compliance
- Custom logic: Modify behavior at specific points (advanced)

Implementation Notes:
--------------------
- All hook methods are async and receive RunContextWrapper as first argument
- Hooks don't modify execution flow (use guardrails for validation/blocking)
- Failed hooks log errors but don't halt agent execution
- Both hook types can coexist: RunHooks for global, AgentHooks for specific
"""

import logging
from typing import (
    Any,
    List,
    Optional,
)

from agents import (
    Agent,
    AgentHooks,
    ModelResponse,
    RunContextWrapper,
    RunHooks,
    Tool,
    TResponseInputItem,
)


logger = logging.getLogger(__name__)


# =============================================================================
# HOOKS OVERVIEW
# =============================================================================
# Hooks are callback classes that receive notifications about lifecycle events
# during an agent run. They're useful for:
# - Logging and debugging
# - Metrics and monitoring
# - Custom behavior at specific points
# - Tracing and observability
#
# TWO TYPES OF HOOKS:
# -------------------
# 1. RunHooks - GLOBAL scope (entire run, all agents)
#    - Attached to: Runner.run(..., hooks=MyRunHooks())
#    - Receives events from: Every agent in the run
#    - Use for: Global logging, metrics, monitoring across all agents
#
# 2. AgentHooks - LOCAL scope (single specific agent)
#    - Attached to: Agent(..., hooks=MyAgentHooks())
#    - Receives events from: Only that one agent
#    - Use for: Agent-specific behavior, per-agent logging
#
# COMPARISON:
# -----------
# | Aspect              | RunHooks                  | AgentHooks               |
# |---------------------|---------------------------|--------------------------|
# | Scope               | All agents in run         | Single agent only        |
# | Attached to         | Runner.run(hooks=...)     | Agent(hooks=...)         |
# | on_handoff receives | from_agent, to_agent      | agent, source            |
# | Use case            | Global observability      | Agent-specific behavior  |
# =============================================================================


class MyRunHook(RunHooks):
    """Global run hooks that observe ALL agents in a run.

    Attach to Runner.run() to receive events from every agent:

        await Runner.run(agent, input, hooks=MyRunHook())
    """

    async def on_agent_start(self, context: RunContextWrapper, agent: Agent) -> None:
        """Called when any agent in the run starts execution.

        Args:
            context: The run context (access context.context for your custom data)
            agent: The agent that is starting
        """
        logger.debug("RunHook: Agent '%s' starting", agent.name)

    async def on_agent_end(self, context: RunContextWrapper, agent: Agent, output: Any) -> None:
        """Called when any agent produces a final output.

        Args:
            context: The run context
            agent: The agent that produced output
            output: The final output from the agent
        """
        logger.debug("RunHook: Agent '%s' ended with output: %s", agent.name, output)

    async def on_handoff(self, context: RunContextWrapper, from_agent: Agent, to_agent: Agent) -> None:
        """Called when control transfers from one agent to another.

        Args:
            context: The run context
            from_agent: The agent handing off control
            to_agent: The agent receiving control
        """
        logger.debug("RunHook: Handoff from '%s' to '%s'", from_agent.name, to_agent.name)

    async def on_tool_start(self, context: RunContextWrapper, agent: Agent, tool: Tool) -> None:
        """Called when any tool starts execution.

        Args:
            context: The run context
            agent: The agent that called the tool
            tool: The tool being executed
        """
        logger.debug("RunHook: Tool '%s' started by agent '%s'", tool.name, agent.name)

    async def on_tool_end(self, context: RunContextWrapper, agent: Agent, tool: Tool, result: str) -> None:
        """Called after any tool completes.

        Args:
            context: The run context
            agent: The agent that called the tool
            tool: The tool that completed
            result: The string result from the tool
        """
        logger.debug("RunHook: Tool '%s' ended with result: %s", tool.name, result)

    async def on_llm_start(
        self,
        context: RunContextWrapper,
        agent: Agent,
        system_prompt: Optional[str],
        input_items: List[TResponseInputItem],
    ) -> None:
        """Called just before making an LLM API call.

        Useful for logging prompts, measuring latency, or modifying inputs.

        Args:
            context: The run context
            agent: The agent making the LLM call
            system_prompt: The system prompt being sent (or None)
            input_items: The input messages/items being sent
        """
        logger.debug("RunHook: LLM call starting for agent '%s'", agent.name)

    async def on_llm_end(self, context: RunContextWrapper, agent: Agent, response: ModelResponse) -> None:
        """Called immediately after LLM returns a response.

        Useful for logging responses, tracking token usage, or post-processing.

        Args:
            context: The run context
            agent: The agent that made the call
            response: The ModelResponse from the LLM
        """
        logger.debug("RunHook: LLM call completed for agent '%s'", agent.name)


class MyAgentHook(AgentHooks):
    """Agent-specific hooks that observe only ONE agent.

    Attach to a specific Agent to receive events only from that agent:

        agent = Agent(
            name="MyAgent",
            instructions="...",
            hooks=MyAgentHook(),  # Only this agent's events
        )
    """

    async def on_start(self, context: RunContextWrapper, agent: Agent) -> None:
        """Called when THIS agent starts execution.

        Note: Method is 'on_start' not 'on_agent_start' for AgentHooks.

        Args:
            context: The run context
            agent: This agent (the one the hook is attached to)
        """
        logger.debug("AgentHook: Agent '%s' starting", agent.name)

    async def on_end(self, context: RunContextWrapper, agent: Agent, output: Any) -> None:
        """Called when THIS agent produces final output.

        Note: Method is 'on_end' not 'on_agent_end' for AgentHooks.

        Args:
            context: The run context
            agent: This agent
            output: The final output produced
        """
        logger.debug("AgentHook: Agent '%s' ended with output: %s", agent.name, output)

    async def on_tool_start(self, context: RunContextWrapper, agent: Agent, tool: Tool) -> None:
        """Called when THIS agent starts executing a tool.

        Args:
            context: The run context
            agent: This agent
            tool: The tool being executed
        """
        logger.debug("AgentHook: Tool '%s' started by agent '%s'", tool.name, agent.name)

    async def on_tool_end(self, context: RunContextWrapper, agent: Agent, tool: Tool, result: str) -> None:
        """Called after THIS agent's tool completes.

        Args:
            context: The run context
            agent: This agent
            tool: The tool that completed
            result: The string result from the tool
        """
        logger.debug("AgentHook: Tool '%s' ended with result: %s", tool.name, result)

    async def on_handoff(self, context: RunContextWrapper, agent: Agent, source: Agent) -> None:
        """Called when another agent hands off TO this agent.

        Args:
            context: The run context
            agent: This agent (receiving the handoff)
            source: The agent that handed off to us
        """
        logger.debug("AgentHook: Received handoff from '%s' to '%s'", source.name, agent.name)

    async def on_llm_start(
        self,
        context: RunContextWrapper,
        agent: Agent,
        system_prompt: Optional[str],
        input_items: list[TResponseInputItem],
    ) -> None:
        """Called just before THIS agent makes an LLM call.

        Args:
            context: The run context
            agent: This agent
            system_prompt: The system prompt (or None)
            input_items: The input messages
        """
        logger.debug("AgentHook: LLM call starting for agent '%s'", agent.name)

    async def on_llm_end(self, context: RunContextWrapper, agent: Agent, response: ModelResponse) -> None:
        """Called after THIS agent receives an LLM response.

        Args:
            context: The run context
            agent: This agent
            response: The ModelResponse from the LLM
        """
        logger.debug("AgentHook: LLM call completed for agent '%s'", agent.name)
