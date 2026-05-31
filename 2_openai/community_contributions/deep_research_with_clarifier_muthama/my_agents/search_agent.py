from __future__ import annotations

from typing import Optional
from pydantic import BaseModel, Field, constr, field_validator
from agents import Agent, WebSearchTool, ModelSettings


INSTRUCTIONS = (
    "You are a research assistant. Given a search term, you search the web for that term and "
    "produce a concise summary of the results. The summary must 2-3 paragraphs and less than 300 "
    "words. Capture the main points. Write succintly, no need to have complete sentences or good "
    "grammar. This will be consumed by someone synthesizing a report, so its vital you capture the "
    "essence and ignore any fluff. Do not include any additional commentary other than the summary itself."
)


# Constrained text type for the summary
SummaryText = constr(strip_whitespace=True, min_length=20, max_length=300 * 6)  # rough char bound

class SearchResult(BaseModel):
    """
    Output model for the search agent.
      - summary: plain text containing 2-3 paragraphs with <= 300 words total.
    """
    summary: SummaryText = Field(..., description="Concise 2-3 paragraph summary, <=300 words.")

    @field_validator("summary")
    @classmethod
    def validate_paragraphs_and_length(cls, summary: str) -> str:
        text = summary.strip()

        # 1) Prevent agent labels/preamble
        lowered = text.lower()
        forbidden_prefixes = ("output:", "summary:", "search results:")
        for prefix in forbidden_prefixes:
            if lowered.startswith(prefix):
                raise ValueError("summary must contain only the summary text (no leading labels).")

        # 2) Paragraph count: split on two or more newlines; allow 2-3 paragraphs
        paragraphs = [paragraph.strip() for paragraph in text.split("\n\n") if paragraph.strip()]
        if len(paragraphs) < 2 or len(paragraphs) > 3:
            raise ValueError("summary must be 2–3 paragraphs (separate paragraphs with a blank line).")

        # 3) Word count <= 300
        words = [word for word in text.split() if word.strip()]
        if len(words) > 300:
            raise ValueError(f"summary must be <= 300 words (got {len(words)}).")

        # 4) Heuristic: no instruction-like trailing commentary
        if any(phrase in lowered for phrase in ("for further details", "see also", "references:")):
            # not strictly forbidden, but likely indicates extra commentary
            raise ValueError("summary appears to include commentary or references; return only the concise summary.")

        return text

# Construct the Agent descriptor
search_agent = Agent(
    name="SearchAgent",
    instructions=INSTRUCTIONS,
    tools=[WebSearchTool(search_context_size="low")],
    model="gpt-4o-mini",
    model_settings=ModelSettings(tool_choice="required"),
    # output_type=SearchResult,
)

# search_agent = Agent(
#     name="Search agent",
#     instructions=INSTRUCTIONS,
#     tools=[WebSearchTool(search_context_size="low")],
#     model="gpt-4o-mini",
#     model_settings=ModelSettings(tool_choice="required"),
# )