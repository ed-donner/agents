from __future__ import annotations

import logging
import re
from typing import List, Optional
from pydantic import BaseModel, Field, constr, field_validator, model_validator
from agents import Agent

logger = logging.getLogger("contextualizer_agent")
logger.addHandler(logging.NullHandler())


INSTRUCTIONS = (
    "You are an expert in refining and contextualizing user queries based on additional clarifying information.\n\n"
    "You will be provided with the following:\n"
    "- The original query from the user\n"
    "- The user's initial answer (if any)\n"
    "- A list of clarifying questions, each with its stated purpose\n"
    "- The user's answers to each clarifying question\n\n"
    "Your task is to generate a **contextualized version of the query** that thoughtfully integrates the user's answers and the reasoning behind the clarifying questions.\n\n"
    "Guidelines:\n"
    "- Do not concatenate or restate the answers verbatim; synthesize them into a coherent, natural-sounding query.\n"
    "- The contextualized query must clearly express the user’s **intent, context, and goals**.\n"
    "- Expand the original query only with information explicitly provided by the user.\n"
    "- Write in clear, professional, and natural language.\n"
    "- Avoid speculation, assumptions, or filler text.\n"
    "- The final query should be **concise**, no longer than five sentences.\n"
    "- Output **only** the final contextualized query—no explanations or preamble.\n\n"
    "### Example\n"
    "**Input:**\n"
    "Original query: How can I improve my company’s marketing strategy?\n\n"
    "Clarifying questions and purposes:\n"
    "1. What type of company do you run? (Purpose: Determines industry context.)\n"
    "2. Who is your target audience? (Purpose: Identifies key customer segments.)\n"
    "3. What marketing channels are you currently using? (Purpose: Reveals existing efforts to build on.)\n\n"
    "User’s answers:\n"
    "1. A mid-sized e-commerce brand selling eco-friendly home products.\n"
    "2. Primarily environmentally conscious consumers aged 25–40.\n"
    "3. We use Instagram, email newsletters, and Google Ads.\n\n"
    "**Output (contextualized query):**\n"
    "How can a mid-sized e-commerce brand that sells eco-friendly home products improve its marketing strategy "
    "to better reach environmentally conscious consumers aged 25–40, particularly through channels like Instagram, "
    "email newsletters, and Google Ads?\n"
)

# Constraints for short, single-line-ish outputs
ShortText = constr(strip_whitespace=True, min_length=10, max_length=2000)


class ClarifyingQA(BaseModel):
    """One clarifying question, its purpose, and the user's answer."""

    question: ShortText = Field(..., description="The clarifying question that was asked.")
    purpose: ShortText = Field(..., description="One-line purpose of the clarifying question.")
    answer: Optional[ShortText] = Field(None, description="The user's answer to this question.")

    @field_validator("answer")
    @classmethod
    def normalize_empty_answer(cls, answer: Optional[str]) -> Optional[str]:
        if answer is None:
            return None
        answer = answer.strip()
        return answer or None


class ContextualizerInput(BaseModel):
    """All inputs provided to the contextualizer."""

    original_query: ShortText = Field(..., description="The user's original query.")
    clarifying_qa: List[ClarifyingQA] = Field(
        default_factory=list,
        description="List of clarifying Q/A pairs (question, purpose, answer).",
    )

    @model_validator(mode="after")
    def ensure_consistency(self) -> "ContextualizerInput":
        # Quick guard: avoid excessive clarifying data (reasonable cap)
        if len(self.clarifying_qa) > 10:
            raise ValueError("No more than 10 clarifying Q/A pairs are supported in a single request.")
        return self


class ContextualizedQuery(BaseModel):
    """
    Output model: a single contextualized query string.
    This model enforces the 'output-only' requirement and the <=5 sentence rule.
    """

    contextualized_query: ShortText = Field(..., description="Final contextualized query (max 5 sentences).")

    @field_validator("contextualized_query")
    @classmethod
    def clean_and_validate(cls, contextualized_query: str) -> str:
        # Prohibit leading labels or extraneous commentary from the LLM
        forbidden_prefixes = (
            "output:",
            "contextualized query:",
            "contextualized:",
            "final query:",
            "answer:",
        )
        low = contextualized_query.lower().lstrip()
        for p in forbidden_prefixes:
            if low.startswith(p):
                raise ValueError("Output must contain only the contextualized query string (no labels or preamble).")

        # Remove stray quotation marks around the whole output
        if (contextualized_query.startswith('"') and contextualized_query.endswith('"')) or (contextualized_query.startswith("'") and contextualized_query.endswith("'")):
            contextualized_query = contextualized_query[1:-1].strip()

        # Enforce sentence count <= 5 (approximate by splitting on sentence terminators)
        terminators = ".!?"
        # naive split: count occurrences of terminators that end sentences
        sentences = [sentence for sentence in _split_sentences(contextualized_query) if sentence.strip()]
        if len(sentences) > 5:
            raise ValueError("Contextualized query must be no longer than five sentences.")
        return contextualized_query.strip()


def _split_sentences(text: str) -> List[str]:
    """
    Lightweight sentence splitter: splits on ., ?, ! followed by space or end-of-string.
    Keeps abbreviations naive risk low (acceptable for validation heuristics).
    """

    # Split at sentence terminators followed by whitespace or end of string
    parts = re.split(r'(?<=[\.\?\!])\s+(?=[A-Z0-9"\'\(\[])|(?<=[\.\?\!])$', text)
    # Fallback: if splitting yields single chunk, try simpler split
    if len(parts) == 1:
        parts = re.split(r'(?<=[\.\?\!])\s+', text)
    return [part.strip() for part in parts if part is not None]


def validate_model_output(raw: dict) -> ContextualizedQuery:
    """
    Validate raw LLM output (dict) and return a typed ContextualizedQuery.
    Raises pydantic.ValidationError on invalid output.
    """
    logger.debug("Validating contextualizer model output")
    return ContextualizedQuery.model_validate(raw)


contextualizing_agent = Agent(
    name="ContextualizerAgent",
    instructions=INSTRUCTIONS,
    model="gpt-4o-mini",
    output_type=ContextualizedQuery,
)