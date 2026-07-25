from dataclasses import dataclass
from autogen_core import AgentId
from typing import Optional

import random

_REGISTERED_AGENT_NAMES: set[str] = set()


@dataclass
class Message:
    content: str


def register_agent_name(agent_name: str) -> None:
    if agent_name != "agent":
        _REGISTERED_AGENT_NAMES.add(agent_name)


def registered_agent_names() -> list[str]:
    return sorted(_REGISTERED_AGENT_NAMES)


def find_recipient(exclude: Optional[str] = None) -> Optional[AgentId]:
    agent_names = registered_agent_names()
    if exclude:
        agent_names = [name for name in agent_names if name != exclude]

    if not agent_names:
        print("No registered peer agents available for refinement")
        return None

    agent_name = random.choice(agent_names)
    print(f"Selecting agent for refinement: {agent_name}")
    return AgentId(agent_name, "default")
