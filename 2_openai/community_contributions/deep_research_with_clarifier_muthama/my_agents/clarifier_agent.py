from __future__ import annotations

import logging
from typing import List, Optional
from pydantic import BaseModel, Field, constr, field_validator, model_validator
from agents import Agent

logger = logging.getLogger("clarifier_agent")
logger.addHandler(logging.NullHandler())

INSTRUCTIONS = (
    "You are a senior research consultant who specializes in formulating clarifying questions for ambiguous or high-level user queries.\n\n"
    "You will be provided with the user's **original query**.\n"
    "Your goal is to craft exactly **three clarifying questions** that will help the user provide the necessary context to refine and improve their query.\n\n"
    "For each question, include a **one-line explanation** describing the *purpose* of the question — specifically, how it will help clarify the user’s needs or intent.\n\n"
    "Guidelines:\n"
    "- Ask exactly three open-ended questions.\n"
    "- Keep each question concise, relevant, and easy to understand.\n"
    "- Avoid leading the user toward a specific answer.\n"
    "- Do not include overly technical or confusing terminology.\n"
    "- Ensure that at least one question helps gauge the user’s **level of expertise** or familiarity with the subject.\n"
    "- Cover different aspects of clarification — such as the user’s goal, scope, and context.\n"
    "- Output your response as **three numbered questions**, each followed by a short *Purpose* line.\n"
    "- Do not include any other commentary or formatting.\n\n"
    "### Example\n"
    "**Input:**\n"
    "Original query: How can I implement machine learning in my company?\n\n"
    "**Output:**\n"
    "1. What specific business challenges are you hoping machine learning will address?\n"
    "   *Purpose: Helps identify the key problem areas where ML could provide value.*\n\n"
    "2. Do you already have any existing data infrastructure or datasets available for analysis?\n"
    "   *Purpose: Determines the feasibility and scope of ML implementation based on data readiness.*\n\n"
    "3. What is your level of experience with data science or machine learning concepts?\n"
    "   *Purpose: Adjusts the complexity and technical depth of possible solutions based on user expertise.*\n"
)

# Constrained string types help enforce short one-line fields and avoid accidental multi-line or huge inputs.
OneLine = constr(strip_whitespace=True, min_length=5, max_length=240)
ClarifyingQuestionText = constr(strip_whitespace=True, min_length=10, max_length=240)


class CreateQuestions(BaseModel):
    clarifying_question: ClarifyingQuestionText = Field(
        ..., description="A concise, open-ended clarifying question (should typically end with a '?')."
    )
    question_purpose: OneLine = Field(
        ..., description="One-line explanation describing why the question helps refine the query."
    )

    @field_validator("clarifying_question")
    def ensure_open_ended(cls, clarifying_question: str) -> str:
        # Ensure it looks like a question and is open-ended; disallow leading yes/no phrases
        if not clarifying_question.endswith("?"):
            raise ValueError("clarifying_question should end with a question mark ('?').")
        return clarifying_question


class ClarifyingQuestions(BaseModel):
    """A set of three validated clarifying questions."""

    questions: List[CreateQuestions] = Field(..., description="Exactly three clarifying questions with purposes.")

    @model_validator(mode="after")
    def validate_questions(self) -> "ClarifyingQuestions":
        if len(self.questions) != 3:
            raise ValueError("Exactly three clarifying questions are required.")

        expertise_keywords = ("experience", "familiar", "level", "expertise", "skill", "knowledge")
        has_expertise_question = any(
            any(k in (q.clarifying_question + " " + q.question_purpose).lower() for k in expertise_keywords)
            for q in self.questions
        )

        if not has_expertise_question:
            raise ValueError("At least one question must assess the user's expertise or familiarity.")

        return self


def validate_model_output(raw: dict) -> ClarifyingQuestions:
    """Validate and parse raw LLM output into a strongly typed ClarifyingQuestions object."""
    logger.debug("Validating ClarifierAgent model output structure")
    return ClarifyingQuestions.model_validate(raw)


clarifier_agent = Agent(
    name="ClarifierAgent",
    instructions=INSTRUCTIONS,
    model="gpt-4o-mini",
    output_type=ClarifyingQuestions,
)