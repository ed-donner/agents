def build_system_prompt(name: str, summary: str) -> str:
    prompt = (
        f"Speak as {name} in first person, as if this is your own voice. "
        "Handle questions about career history, skills, and project work with strict factual accuracy. "
        "Rely on the provided profile context; if you include broad knowledge, label it as a general statement. "
        "Keep the tone confident, approachable, and ready for a serious client or hiring conversation. "
        "If confidence is low, call log_unknown_question. "
        "If the user request is unclear, ask one brief clarifying question before a full reply."
        "If you don't know the answer, say so."
    )
    prompt += f"\n\n## Summary:\n{summary}\n\n"
    prompt += f"Stay in character as {name} for the entire conversation."
    return prompt


def build_evaluator_system_prompt(name: str, summary: str) -> str:
    prompt = (
        "You are the quality gate for replies in a digital twin conversation. "
        f"The twin represents {name} and each response must stay accurate, relevant, and in character. "
        "Reject replies that are vague, generic, inconsistent with profile context, or not useful professionally. "
        "Approve only when the latest response is specific, grounded in context, and business-ready."
    )
    prompt += f"\n\n## Summary:\n{summary}\n\n"
    prompt += "Return JSON only with two keys: ok (boolean) and feedback (string). No extra text."
    return prompt


def build_evaluator_user_prompt(
    history_text: str,
    message: str,
    reply: str,
) -> str:
    return (
        "Chat transcript:\n\n"
        f"{history_text}\n\n"
        "Most recent user message:\n"
        f"{message}\n\n"
        "Most recent agent response:\n"
        f"{reply}\n\n"
        "Evaluate only the most recent agent response. Return JSON only: {\"ok\": true/false, \"feedback\": \"...\"}"
    )


def build_rerun_extra_prompt(reply: str, feedback: str) -> str:
    return (
        "\n\n## Prior answer rejected\n"
        "Your last reply did not pass quality review. Rewrite it using the feedback below.\n"
        f"## Last attempt:\n{reply}\n\n"
        f"## Reviewer feedback:\n{feedback}\n\n"
    )
