from autogen_core.tools import FunctionTool


def get_style_guide() -> str:
    return (
        "Style guide:\n"
        "- Keep it under 120 words\n"
        "- Be professional and direct\n"
        "- Use one specific benefit\n"
        "- End with a single CTA\n"
    )


def word_count(text: str) -> str:
    count = len(text.split())
    return f"Word count: {count}"


style_guide_tool = FunctionTool(
    get_style_guide,
    description="Get the email style guide",
    strict=True,
)

word_count_tool = FunctionTool(
    word_count,
    description="Count words in a given text",
    strict=True,
)
