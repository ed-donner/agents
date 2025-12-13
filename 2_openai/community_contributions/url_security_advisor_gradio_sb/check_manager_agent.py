from agents import Agent

check_manager_instruction = """You are security manager in the field of IT software security
      Follow these steps carefuly:
      1. Analyze two security checks about provided url 
      2. Evaluate and select
        Review a check and choose single best one using your judgement of which one is most effective.
      3. Handoff for Sending
        Return only winning ckeck
Crucial Rules:
- You must use generated checks — do not write them yourself.
- You must hand off exactly ONE security check text - never more than one.
"""

check_manager_agent = Agent(
    name="Security Manager",
    instructions=check_manager_instruction,
    model="gpt-4o-mini",
)
