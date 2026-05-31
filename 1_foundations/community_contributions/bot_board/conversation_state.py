from enum import Enum

class ConversationState(Enum):
    """Enumeration of conversation states for a bot/agent workflow."""

    OPEN = "open"
    QUESTION = "question"
    ANSWER = "answer"
    EVALUATION = "evaluation"
    DECISION = "decision"
    SUMMARY = "summary"
    CLOSE = "close"

    def __str__(self) -> str:  # convenient for f-strings and logs
        return self.value

    def next_state(self) -> "ConversationState":
        """Return the next state in the conversation workflow.

        Workflow sequence:
        OPEN → QUESTION → ANSWER → EVALUATION → DECISION → SUMMARY → CLOSE
        CLOSE is terminal and returns itself.
        """
        order = [
            ConversationState.OPEN,
            ConversationState.QUESTION,
            ConversationState.ANSWER,
            ConversationState.EVALUATION,
            ConversationState.DECISION,
            ConversationState.SUMMARY,
            ConversationState.CLOSE,
        ]
        try:
            idx = order.index(self)
        except ValueError:
            # Fallback: if somehow an unknown state, return CLOSE to be safe
            return ConversationState.CLOSE
        # If already at the end, remain at CLOSE
        return order[min(idx + 1, len(order) - 1)]
