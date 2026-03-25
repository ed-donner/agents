"""Specialist agents: researcher (tools), judge (structured), content builder (markdown course)."""

from agents import Agent, ModelSettings

from config import MODEL
from schemas import JudgeFeedback
from tools import google_search

RESEARCHER_INSTRUCTIONS = """
You are an expert researcher. Your goal is to find comprehensive and accurate information on the user's topic.
Use the `google_search` tool to find relevant information.
Summarize your findings clearly in plain text (several paragraphs are fine).
If you receive feedback that your research is insufficient, use the feedback to refine your next search queries and deepen the summary.
Do not invent sources; ground claims in what the search tool returns.
"""

JUDGE_INSTRUCTIONS = """
You are a strict editor.
You receive the user's original request and the researcher's `research_findings`.
If the findings are missing key information needed to teach the topic, or are too shallow, return status='fail' with concrete guidance.
If they are sufficiently complete and accurate for building a course module, return status='pass' with a brief confirmation.
"""

CONTENT_BUILDER_INSTRUCTIONS = """
You are an expert course creator.
Take the approved research findings and transform them into a well-structured, engaging course module.

**Formatting rules:**
1. Start with a main title using a single `#` (H1).
2. Use `##` for main section headings.
3. Use bullet points and clear paragraphs.
4. Maintain a professional but engaging tone.

Ensure the content directly addresses the user's original request.
"""


def build_researcher() -> Agent:
    return Agent(
        name="researcher",
        instructions=RESEARCHER_INSTRUCTIONS.strip(),
        model=MODEL,
        tools=[google_search],
        model_settings=ModelSettings(tool_choice="auto"),
    )


def build_judge() -> Agent[JudgeFeedback]:
    return Agent(
        name="judge",
        instructions=JUDGE_INSTRUCTIONS.strip(),
        model=MODEL,
        output_type=JudgeFeedback,
    )


def build_content_builder() -> Agent:
    return Agent(
        name="content_builder",
        instructions=CONTENT_BUILDER_INSTRUCTIONS.strip(),
        model=MODEL,
    )


researcher_agent = build_researcher()
judge_agent = build_judge()
content_builder_agent = build_content_builder()
