from dataclasses import dataclass
from autogen_core import AgentId
import glob
import os
import random


@dataclass
class Message:
    content: str


def find_recipient() -> AgentId:
    """Pick a random already-registered interviewer agent to bounce questions off."""
    try:
        agent_files = glob.glob("agent*.py")
        agent_names = [os.path.splitext(f)[0] for f in agent_files]
        agent_names.remove("agent")  # exclude the template
        agent_name = random.choice(agent_names)
        print(f"  Passing questions to {agent_name} for refinement")
        return AgentId(agent_name, "default")
    except Exception as e:
        print(f"  Could not find a recipient ({e}), keeping original questions")
        return AgentId("agent1", "default")
