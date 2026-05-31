log_unknown_question_json = {
    "name": "log_unknown_question",
    "description": "Log unanswered questions for later follow-up.",
    "parameters": {
        "type": "object",
        "properties": {
            "question": {"type": "string", "description": "Question that lacked reliable context"},
        },
        "required": ["question"],
        "additionalProperties": False,
    },
}

TOOLS = [
    {"type": "function", "function": log_unknown_question_json},
]
