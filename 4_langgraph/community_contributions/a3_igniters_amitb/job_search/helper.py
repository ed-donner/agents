from typing import List, Any
from langchain_core.messages import HumanMessage, AIMessage


def format_conversation(messages: List[Any]) -> str:
    """
    Format the conversation history for readability.
    Args:
        messages: The list of messages to format
    Returns:
        The formatted conversation history
    """
    conversation = "Conversation history:\n\n"
    for message in messages:
        if isinstance(message, HumanMessage):
            conversation += f"User: {message.content}\n"
        elif isinstance(message, AIMessage):
            text = message.content or "[Tools use]"
            conversation += f"Assistant: {text}\n"
    return conversation
