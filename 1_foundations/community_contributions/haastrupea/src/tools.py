from ultils.Pushover import PushOver


class Tools:
    def __init__(self, notifier: PushOver) -> None:
        self.notifier = notifier


    def record_user_details(self, email: str, name: str, notes: str) -> dict:

        self.notifier.push_notification(f"New Contact: {name} <{email}>\nInterest: {notes}")
        return {"recorded": "ok", "message": f"Perfect! Thanks {name}. I'll be in touch soon."}

    def record_unknown_question(self, question: str) -> dict:
        self.notifier.push_notification(f"Unanswered: {question}")
        return {"recorded": "ok", "message": "I'll make a note of that question."}


    def get_tools (self):
        tools = [
            {
                "type": "function",
                "function": {
                    "name": "record_user_details",
                    "description": "Record user contact information. it is important that you ask for their name if they haven't provided it yet. Only call this tool after you have collected both email and name.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "email": {"type": "string", "description": "The email address of this user"},
                            "name": {"type": "string", "description": "The user's full name"},
                            "notes": {"type": "string", "description": "A brief 1-line summary of what the user was asking about or interested in"}
                        },
                        "required": ["email", "name", "notes"],
                        "additionalProperties": False
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "record_unknown_question",
                    "description": "Always use this tool to record any question that couldn't be answered",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "question": {"type": "string", "description": "The question that couldn't be answered"}
                        },
                        "required": ["question"],
                        "additionalProperties": False
                    }
                }
            },
        ]
        return tools