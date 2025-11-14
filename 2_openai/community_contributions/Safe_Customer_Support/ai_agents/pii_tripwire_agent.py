from agents import Agent

class PIITripwireAgent:
    def __init__(self):
        self.agent = Agent(
            name="PII Tripwire Agent",
            model="gpt-4o-mini",
            instructions=(
                "You are the PII Tripwire Agent. You take over whenever "
                "a safety or policy violation occurs (for example, if PII was detected). "
                "Calmly explain that the user's message contained restricted information, "
                "reassure them, and guide them to continue safely. "
                "Never mention Tripwire, internal systems, or guardrails explicitly."
            ),
        )
