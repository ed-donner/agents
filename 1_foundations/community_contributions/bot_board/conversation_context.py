from typing import List, Dict, Optional, Callable
from collections import defaultdict
from conversation_state import ConversationState
from conversation_role import ConversationRole
from IPython.display import Markdown, display

class ConversationContext:
    """Holds the current conversation state and its LLM-compatible context.

    Adds a per-state callbacks registry. You can register a callback for a specific
    ConversationState via add_callback(state, callback). Whenever add_response is called,
    all callbacks registered for the current conversation_state will be invoked with the
    response content as a single argument.
    """
    def __init__(self, conversation_state: ConversationState, context: Optional[List[Dict[str, str]]] = None):
        self.conversation_state = conversation_state
        self.context: List[Dict[str, str]] = context or []
        self.subject = None
        # Callbacks registry: state -> list[callback(content:str) -> None]
        self._callbacks: Dict[ConversationState, List[Callable[[str], None]]] = defaultdict(list)

    def reset(self):
        self.conversation_state = ConversationState.OPEN
        self.context = []
        self._callbacks = defaultdict(list)

    def set_conversation_state(self, conversation_state: ConversationState, context: Optional[List[Dict[str, str]]] = None):
        """Update the conversation state along with a list of role/content dicts."""
        self.conversation_state = conversation_state

        if context is not None:
            self.context = context

    def add_callback(self, conversation_state: ConversationState, callback: Callable[[str], None]):
        """Register a callback to be invoked when add_response is called in a given state.

        Args:
            conversation_state: The ConversationState for which this callback should be triggered.
            callback: A function accepting a single str argument (the content) and returning None.
        """
        if conversation_state is None or callback is None:
            return
        self._callbacks[conversation_state].append(callback)

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
        if content is None or content == "":
            return
        self.context.append({"role": role, "content": content})
        # Trigger callbacks for the current state with the content
        callbacks = self._callbacks.get(self.conversation_state, [])
        for cb in list(callbacks):  # copy to avoid mutation issues during iteration
            try:
                cb(content)
            except Exception:
                pass

    def print_context(self, separator: str = "\n\n"):
        """Print only the text content of all context messages, separated by a delimiter.

        Args:
            separator: String used to separate messages when printing.
        Returns:
            The combined string that was printed.
        """
        texts = [msg.get("content", "") for msg in self.context]
        combined = separator.join(texts)
        # Print for convenience as requested
        display(Markdown(combined))

    def should_participate(self, conversation_role: ConversationRole) -> bool:
        match self.conversation_state:
            case ConversationState.OPEN:
                return True
            case ConversationState.QUESTION:
                return conversation_role == ConversationRole.CHAIRMAN
            case ConversationState.ANSWER:
                return conversation_role == ConversationRole.EXPERT
            case ConversationState.EVALUATION:
                return conversation_role == ConversationRole.AUDITOR
            case ConversationState.DECISION:
                return conversation_role == ConversationRole.CHAIRMAN
            case ConversationState.SUMMARY:
                return conversation_role == ConversationRole.SECRETARY
            case ConversationState.CLOSE:
                return True
