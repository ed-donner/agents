"""HALI MCP server — HPV Awareness & Learning Initiative (Kenya). Stdio transport."""

import os
import sys

import requests
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("hali_server")


def push(message: str) -> None:
    print(f"[PUSH] {message}", file=sys.stderr, flush=True)
    user, token = os.getenv("PUSHOVER_USER"), os.getenv("PUSHOVER_TOKEN")
    if user and token:
        requests.post(
            "https://api.pushover.net/1/messages.json",
            data={"user": user, "token": token, "message": message},
        )


@mcp.tool()
async def check_eligibility(age: int, gender: str = "female", prior_doses: int = 0) -> dict:
    """Check HPV vaccine eligibility under Kenya's national programme (single-dose schedule)."""
    female_terms = {"female", "girl", "woman", "msichana", "mwanamke", "f"}
    if gender.lower() in female_terms:
        if prior_doses >= 1:
            return {
                "eligible": False,
                "message": "Already vaccinated — one dose is sufficient under Kenya's current schedule.",
                "age": age,
            }
        if 10 <= age <= 14:
            return {
                "eligible": True,
                "message": (
                    "Eligible for routine HPV vaccination. "
                    "Free at school or nearest health facility. Single dose."
                ),
                "age": age,
            }
        if age > 14:
            return {
                "eligible": True,
                "message": (
                    "Eligible for catch-up HPV vaccination at a health facility. "
                    "Single dose, free of charge."
                ),
                "age": age,
            }
        return {
            "eligible": False,
            "message": "Below minimum age (10). Check back when the child turns 10.",
            "age": age,
        }
    return {
        "eligible": False,
        "message": (
            "Kenya's HPV programme currently targets girls and women. "
            "Boys/men: consult a health worker."
        ),
        "age": age,
    }


@mcp.tool()
async def record_interest(
    name: str,
    location: str,
    contact: str = "not provided",
    notes: str = "not provided",
) -> dict:
    """Record someone who wants HPV vaccination or more information."""
    push(f"New interest: {name} in {location} | Contact: {contact} | Notes: {notes}")
    return {"recorded": "ok", "message": "Details recorded. A health worker will be in touch."}


@mcp.tool()
async def record_unknown_question(question: str, mode: str = "caregiver") -> dict:
    """Log a question you cannot answer safely — use instead of guessing."""
    push(f"[{mode.upper()} - UNANSWERED] {question}")
    return {"recorded": "ok"}


if __name__ == "__main__":
    mcp.run(transport="stdio")
    