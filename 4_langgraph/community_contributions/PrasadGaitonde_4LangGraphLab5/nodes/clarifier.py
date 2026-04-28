"""
Clarifier Node for the Intelligent Data Analysis Agent.
Generates 3 clarifying questions before starting analysis.
"""
from typing import Dict, Any, List
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field
from config import CLARIFIER_MODEL, CLARIFYING_QUESTION_COUNT


class ClarifyingQuestions(BaseModel):
    """Output schema for clarifying questions."""
    questions: List[str] = Field(
        default_factory=list,
        description=f"Exactly {CLARIFYING_QUESTION_COUNT} clarifying questions to better understand the user's data analysis request",
        min_items=CLARIFYING_QUESTION_COUNT,
        max_items=CLARIFYING_QUESTION_COUNT
    )
    ready_to_proceed: bool = Field(
        default=False,
        description="False because we always ask clarifying questions first"
    )


class ClarifierNode:
    """Node that generates clarifying questions for data analysis requests."""

    def __init__(self):
        self.llm = ChatOpenAI(model=CLARIFIER_MODEL)
        self.structured_llm = self.llm.with_structured_output(ClarifyingQuestions, method="function_calling")

    def generate_system_prompt(self) -> str:
        """Generate the system prompt for the clarifier."""
        return f"""You are a Clarifier assistant for a data analysis system.
Your job is to understand a user's data analysis request and ask exactly {CLARIFYING_QUESTION_COUNT} clarifying questions
that will help generate accurate SQL queries and analysis.

Your questions should:
1. Identify which tables or data sources are relevant
2. Clarify ambiguous terms or metrics the user mentions
3. Understand the time period, filters, or grouping they want
4. Determine the format or type of output they expect

Ask exactly {CLARIFYING_QUESTION_COUNT} questions. Make them specific and actionable.
Do not ask questions that could be answered by inspecting the database schema.
"""

    def __call__(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate clarifying questions based on the user's request.

        Args:
            state: Current state containing user's message

        Returns:
            Updated state with clarifying questions
        """
        # Get the user's original request
        messages = state.get("messages", [])
        user_request = None

        for msg in messages:
            if hasattr(msg, "role") and msg.role == "user":
                user_request = msg.content
                break

        if not user_request:
            user_request = str(messages[-1]) if messages else "No request provided"

        # Generate clarifying questions
        system_prompt = self.generate_system_prompt()

        user_prompt = f"""The user has made the following data analysis request:

"{user_request}"

Generate {CLARIFYING_QUESTION_COUNT} specific clarifying questions that will help
write accurate SQL queries to answer this request."""

        clarifier_messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ]

        result = self.structured_llm.invoke(clarifier_messages)

        # Format questions for display
        questions_text = "\n".join([f"{i+1}. {q}" for i, q in enumerate(result.questions)])

        return {
            "clarifying_questions": result.questions,
            "questions_text": questions_text,
            "awaiting_user_clarification": True,
            "messages": [{
                "role": "assistant",
                "content": f"Before I can analyze your data request, I need some clarification:\n\n{questions_text}"
            }]
        }


def clarifier_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """Standalone clarifier node function."""
    clarifier = ClarifierNode()
    return clarifier(state)
