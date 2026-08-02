from dataclasses import dataclass
from autogen_core import AgentId
import glob
import os
import random

@dataclass
class Message:
    content: str


def find_recipient() -> AgentId:
    """Find a random agent to bounce ideas off for refinement"""
    try:
        # Find all agent files (exclude creator files and base templates)
        agent_files = glob.glob("agent*.py")
        agent_names = [os.path.splitext(file)[0] for file in agent_files]
        
        # Filter out non-agent files
        exclude_prefixes = ["creator", "agent.py"]  # Exclude creator and base agent template
        agent_names = [
            name for name in agent_names 
            if not name.startswith("creator") and name != "agent"
        ]
        
        if not agent_names:
            print("No other agents found for refinement")
            return AgentId("agent1", "default")
        
        agent_name = random.choice(agent_names)
        print(f"Selecting agent for refinement: {agent_name}")
        return AgentId(agent_name, "default")
    except Exception as e:
        print(f"Exception finding recipient: {e}")
        return AgentId("agent1", "default")
