"""Schemas for the module 2 email campaign workflow."""

from typing import Literal
from pydantic import BaseModel, Field


class ColdEmail(BaseModel):
    """Structured email draft."""

    subject: str = Field(min_length=8, max_length=120)
    preview_text: str = Field(min_length=12, max_length=160)
    body_text: str = Field(min_length=80)
    cta: str = Field(min_length=8, max_length=120)
    tone: Literal["serious", "engaging", "concise", "playful"]


class NameCheckOutput(BaseModel):
    """Personal name detection output."""

    is_name_in_message: bool
    name: str


class SafetyReviewOutput(BaseModel):
    """Output policy review result."""

    blocked: bool
    reason: str


class Contact(BaseModel):
    """Contact information."""
    name: str
    email: str
    company: str


class EmailPayload(BaseModel):
    """Message envelope for a send operation."""
    to: str
    subject: str
    html: str
