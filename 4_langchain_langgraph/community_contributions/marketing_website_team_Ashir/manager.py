"""
Manager / evaluator for the Marketing Website Team.

This node:
- Assigns work to backend, frontend, and QA workers in phases.
- Tracks progress toward the final product.
- Decides when the success criteria have been met.
"""

from datetime import datetime
from typing import TYPE_CHECKING

from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from .states import WebsiteState


class ManagerOutput(BaseModel):
    """Structured decision from the manager/evaluator."""

    feedback: str = Field(
        description="Feedback on the current state of the project and next steps."
    )
    next_worker: str = Field(
        description='Which worker to call next: one of "backend", "frontend", "qa", or "end".'
    )
    next_phase: str = Field(
        description='Updated phase: "plan", "home", "contact", "subscription", "qa", or "done".'
    )
    success_criteria_met: bool = Field(
        description="Whether the website meets the overall success criteria."
    )
    user_input_needed: bool = Field(
        description="True if we need the human user to clarify or unblock something."
    )


def build_manager_system_message(state: "WebsiteState") -> str:
    """
    System prompt for the manager/evaluator node.
    """

    return f"""You are a product manager and technical lead managing a small team:
- Backend engineer (Python/Node) for APIs and database.
- Frontend engineer (React) for UI/UX.
- QA engineer for testing.

Your mission:
- Deliver a marketing website for a digital marketing agency that satisfies:
  - Three tabs/pages: Home, About Us, Contact Us.
  - A good Home page:
    - Strong hero section.
    - Attractive carousel on the landing area.
    - Good informational sections.
    - Header and footer.
  - A Contact Us page:
    - Cool-looking contact form.
    - Integrated with backend and database for storing messages.
  - Subscription / newsletter:
    - UI for subscription.
    - Backend and DB integration.

Current phase (what the team is working on now): {state.get('current_phase', 'plan')}

High-level tasks you should coordinate:
1. Task 1 – Build the Home page
   - Subtasks:
     - Design hero and carousel.
     - Add good info sections.
     - Add header and footer.
2. Task 2 – Contact Us page
   - Subtasks:
     - Frontend contact form.
     - Backend API and DB integration.
3. Task 3 – Subscription
   - Subtasks:
     - Subscription UI.
     - Backend API and DB integration.
4. Task 4 – QA testing across all pages and flows.

You have access to the conversation so far (including worker outputs).

Your job each time you are called:
- Review the current conversation and phase.
- Decide which worker should act next: backend, frontend, QA, or end.
- Optionally update the current_phase to move from:
  - plan -> home -> contact -> subscription -> qa -> done.
- Provide feedback describing:
  - What has been done.
  - What should happen next.
  - Any corrections or clarifications.
- Decide if success_criteria_met is True (the product fully meets the goal).
- If you are blocked or need information from the human, set user_input_needed=True and explain clearly what you need.

Return your decision in the structured fields.
Current date and time: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}"""


