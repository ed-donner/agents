from typing import List, Dict, Optional
from conversation_state import ConversationState

class ConversationContext:
    """Holds the current conversation state and its LLM-compatible context."""
    def __init__(self, conversation_state: ConversationState, context: Optional[List[Dict[str, str]]] = None):
        self.conversation_state = conversation_state
        self.context: List[Dict[str, str]] = context or []

    def set_conversation_state(self, conversation_state: ConversationState, context: Optional[List[Dict[str, str]]] = None):
        """Update the conversation state along with a list of role/content dicts."""
        self.conversation_state = conversation_state

        if context is not None:
            self.context = context

    def get_context(self) -> List[Dict[str, str]]:
        return self.context

    def get_conversation_state(self) -> ConversationState:
        return self.conversation_state

    def get_next_conversation_state(self) -> ConversationState:
        return self.conversation_state.next_state()

    def update_context(self, additional_context: Optional[List[Dict[str, str]]] = None):
        self.conversation_state = self.conversation_state.next_state()
        if additional_context is not None:
            self.context.extend(additional_context)
            
    def add_response(self, content: str, role: Optional[str] = "user"):
        self.context.append({"role": role, "content": content})

    def print_context(self, separator: str = "\n\n---\n\n") -> str:
        """Print only the text content of all context messages, separated by a delimiter.

        Args:
            separator: String used to separate messages when printing.
        Returns:
            The combined string that was printed.
        """
        texts = [msg.get("content", "") for msg in self.context]
        combined = separator.join(texts)
        # Print for convenience as requested
        print(combined)
