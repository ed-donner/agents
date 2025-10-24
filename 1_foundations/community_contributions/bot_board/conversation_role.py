from enum import Enum

class ConversationRole(Enum):
    """Enumeration of conversation role for a bot board member."""

    CHAIRMAN = "chairman"
    EXPERT = "expert"
    AUDITOR = "auditor"
    SECRETARY = "secretary"
    NONE = "none"

    def __str__(self) -> str:  # convenient for f-strings and logs
        return self.value