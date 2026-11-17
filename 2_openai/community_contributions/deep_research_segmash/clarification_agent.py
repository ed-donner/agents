from pydantic import BaseModel, Field
from agents import Agent, handoff
from dotenv import load_dotenv
import os

load_dotenv(override=True)
MODEL_NAME = os.getenv("DEFAULT_MODEL_NAME", "gpt-5.4-mini")

# Maximum number of clarification questions the agent may ask before it must stop.
# MAX_QUESTIONS = 3

INSTRUCTIONS = f"""
You are a research assistant. Given a search query, you should ask the user few questions in order to clarify better the query area
You should ask for questions only if the query is not clear enough.
The questions are not for free text, give the user few options to answer and the user should choose one answer.
In each step you should improve the query and check if needed to ask more question, respond with json: {{"query" : <improved query>, "question": <question>, "options": [<option1>,<option2>,<option3>...]}}

IMPORTANT - when the query is ALREADY clear enough (you have no more questions to ask):
- Do NOT just return an empty question. Instead, HAND OFF BACK to the manager by calling the
  "return_to_manager" handoff.
- When you hand back, pass a short note that the query is now clear and that the manager must NOT
  ask any more clarification questions and should proceed directly with the research
  (plan -> search -> write).
- Example hand-back message: "Query clarified and clear enough: '<improved query>'.
  Do not ask more clarification questions. Proceed to plan_searches now."

Only produce the JSON with "question": null when you are returning control and there is no manager
to hand back to; otherwise prefer the "return_to_manager" handoff.
"""

class ClarificationData(BaseModel):
    query: str = Field(description="The original query or the curent query after improvment")
    question: str | None = Field(default=None, description="A question for the user to clarify the query, or null when no more questions are needed")
    options: list[str] = Field(default_factory=list, description="Suggested options for the clarify question - the user should choose one")

clarification_agent = Agent(name="Clarification_Agent", instructions=INSTRUCTIONS, model=MODEL_NAME,output_type=ClarificationData)


def register_back_handoff(manager_agent) -> None:
    """Attach the 'return_to_manager' handoff back to the manager.

    Called from manager_agent AFTER manager_agent is created, to avoid a circular import
    (clarification_agent must not import manager_agent at module load time).
    """
    back_handoff = handoff(
        manager_agent,
        tool_name_override="return_to_manager",
        tool_description_override=(
            "Hand control back to the research manager when the query is already clear enough and "
            "you have no more clarification questions. Include a note in your hand-back that the "
            "query is clear, that NO more clarification questions are needed, and that the manager "
            "must proceed directly with the research (plan -> search -> write)."
        ),
    )
    # Avoid registering twice if the module is reloaded.
    if not any(getattr(h, "tool_name", None) == "return_to_manager" for h in clarification_agent.handoffs):
        clarification_agent.handoffs.append(back_handoff)
