from __future__ import annotations

import logging
import re
from typing import List

from pydantic import BaseModel, Field, constr, field_validator, model_validator
from agents import Agent

logger = logging.getLogger("writer_agent")
logger.addHandler(logging.NullHandler())

INSTRUCTIONS = (
    "You are a senior researcher tasked with writing a cohesive report for a research query. "
    "You will be provided with the original query, and some initial research done by a research assistant.\n"
    "You should first come up with an outline for the report that describes the structure and "
    "flow of the report. Then, generate the report and return that as your final output.\n"
    "The final output should be in markdown format, and it should be lengthy and detailed. Aim "
    "for 5-10 pages of content, at least 1000 words."
)

ShortLine = constr(strip_whitespace=True, min_length=10, max_length=300)
MarkdownText = constr(strip_whitespace=True, min_length=1000, max_length=20000)
FollowUpQuestion = constr(strip_whitespace=True, min_length=5, max_length=200)


def _count_words(text: str) -> int:
    return len(re.findall(r"\S+", text)) # Conservative word count: split on whitespace


def _count_sentences(text: str) -> int:
    return len([sentence for sentence in re.split(r"[.!?]+", text) if sentence.strip()]) # Simple sentence tokenizer based on ., !, ?


class ReportData(BaseModel):
    """
    Output model for the WriterAgent.
    - short_summary: 2-3 sentence summary (2-3 sentences strongly enforced)
    - markdown_report: full report in Markdown, at least 1000 words
    - follow_up_questions: 1-10 suggested follow-up research topics
    """

    short_summary: ShortLine = Field(..., description="A short 2-3 sentence summary of the findings.")
    markdown_report: MarkdownText = Field(..., description="The final report in Markdown format.")
    follow_up_questions: List[FollowUpQuestion] = Field(
        ..., description="Suggested topics to research further (1-10 items)."
    )

    @field_validator("short_summary")
    @classmethod
    def validate_summary_sentences(cls, short_summary: str) -> str:
        sentences = _count_sentences(short_summary)
        if sentences < 2 or sentences > 10:
            raise ValueError("short_summary must be 2–3 sentences long.")
        # Ensure it's short and summary-like (not multi-paragraph)
        if "\n" in short_summary:
            raise ValueError("short_summary must be a single short paragraph (no newlines).")
        return short_summary.strip()

    @field_validator("markdown_report")
    @classmethod
    def validate_markdown_and_length(cls, markdown_report: str) -> str:
        # Must look like Markdown: require at least one top-level header or other header
        if not re.search(r"(^|\n)#{1,6}\s+\S", markdown_report):
            raise ValueError("markdown_report must contain at least one Markdown header (e.g., '# Title').")

        word_count = _count_words(markdown_report)
        if word_count < 100:
            raise ValueError(f"markdown_report must be at least 100 words (got {word_count}).")
        # Soft upper bound to prevent runaway outputs; adjust if necessary
        if word_count > 20000:
            raise ValueError(f"markdown_report too long (>{20000} words).")
        return markdown_report.strip()

    @field_validator("follow_up_questions")
    @classmethod
    def validate_followups(cls, follow_up_questions: List[str]) -> List[str]:
        if not isinstance(follow_up_questions, list):
            raise ValueError("follow_up_questions must be a list of short suggestion strings.")
        if len(follow_up_questions) < 1:
            raise ValueError("At least one follow-up question is required.")
        if len(follow_up_questions) > 10:
            raise ValueError("No more than 10 follow-up questions are allowed.")
        # Validate each item
        cleaned = []
        for item in follow_up_questions:
            if "\n" in item:
                raise ValueError("Each follow_up_question must be a single-line string.")
            item = item.strip()
            if len(item) < 5:
                raise ValueError("Each follow_up_question must be at least 5 characters.")
            cleaned.append(item)
        return cleaned

    @model_validator(mode="after")
    def cross_check_summary_vs_report(self) -> "ReportData":
        """
        Ensure the short_summary is actually a summary by checking it doesn't simply copy a header
        and that it is proportionally short relative to the report. This is a heuristic guard.
        """
        report_words = _count_words(self.markdown_report)
        summary_words = _count_words(self.short_summary)
        if summary_words > max(200, int(0.05 * report_words)):
            raise ValueError("short_summary is too long relative to the report.")
        return self


def validate_model_output(raw: dict) -> ReportData:
    """
    Parse and validate a raw LLM output dict into ReportData.
    Raises pydantic.ValidationError on invalid output.
    """
    logger.debug("Validating writer model output")
    return ReportData.model_validate(raw)


writer_agent = Agent(
    name="WriterAgent",
    instructions=INSTRUCTIONS,
    model="gpt-4o-mini",
    output_type=ReportData,
)