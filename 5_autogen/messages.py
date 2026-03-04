from dataclasses import dataclass
from autogen_core import AgentId
import random
from typing import Optional

# Only agents that have been registered by the Creator are available for messaging.
REGISTERED_AGENTS: set[str] = set()


@dataclass
class Message:
    content: str


def register_agent(name: str) -> None:
    """Call when the Creator has registered an agent with the runtime."""
    REGISTERED_AGENTS.add(name)


def find_recipient(exclude: Optional[str] = None) -> Optional[AgentId]:
    """Pick a random agent that is registered and available. Exclude the current agent."""
    try:
        candidates = (
            REGISTERED_AGENTS - {exclude} if exclude else set(REGISTERED_AGENTS)
        )
        if not candidates:
            return None
        agent_name = random.choice(list(candidates))
        print(f"Selecting agent for refinement: {agent_name}")
        return AgentId(agent_name, "default")
    except Exception as e:
        print(f"Exception finding recipient: {e}")
        return None
