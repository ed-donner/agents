from dataclasses import dataclass
from autogen_core import AgentId
import glob
import os
import random

@dataclass
class Message:
    content: str

def find_recipient(agent_id) -> AgentId:
    print(agent_id)
    try:
        agent_files = glob.glob("doctor*.py")
        agent_names = [os.path.splitext(file)[0] for file in agent_files]
        agent_name = random.choice(agent_names)
        while agent_id==agent_name:
            agent_name = random.choice(agent_names)
        print(f"Selecting agent for refinement: {agent_name}")
        return AgentId(agent_name, "default")
    except Exception as e:
        print(f"Exception finding recipient: {e}")
