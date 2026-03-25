

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any
from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel, Field

from health_rules import CONDITION_HINTS, RED_FLAGS

_DIR = Path(__file__).resolve().parent
if str(_DIR) not in sys.path:
    sys.path.insert(0, str(_DIR))



mcp = FastMCP("health_intake_triage")

DISCLAIMER = (
    "This output is for education and organization of information only. "
    "It is not a diagnosis or treatment plan. Only a qualified clinician who examines you "
    "can diagnose or prescribe. If you might be having an emergency, call your local emergency number."
)


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").strip().lower())


def _score_conditions(blob: str) -> list[dict[str, Any]]:
    scored: list[tuple[int, str, str]] = []
    for label, keywords, summary in CONDITION_HINTS:
        hits = sum(1 for k in keywords if k in blob)
        if hits:
            scored.append((hits, label, summary))
    scored.sort(key=lambda x: -x[0])
    out: list[dict[str, Any]] = []
    for hits, label, summary in scored[:6]:
        out.append(
            {
                "possible_topic": label,
                "keyword_overlap_score": hits,
                "educational_note": summary,
            }
        )
    return out


def _red_flags(blob: str) -> list[dict[str, str]]:
    alerts: list[dict[str, str]] = []
    for phrase, severity, message in RED_FLAGS:
        if phrase in blob:
            alerts.append({"severity": severity, "matched_cue": phrase, "message": message})
    return alerts


def _urgency_tier(alerts: list[dict[str, str]]) -> str:
    if any(a["severity"] == "emergency" for a in alerts):
        return "emergency"
    if any(a["severity"] == "urgent" for a in alerts):
        return "urgent"
    return "non_urgent_routine_or_self_care"


def _missing_fields(data: dict[str, str]) -> list[str]:
    optional_priority = [
        ("chief_complaint", "Main problem in the patient's own words"),
        ("onset_and_course", "When it started and how it changed"),
        ("severity", "Severity (e.g. 0–10) or impact on daily activities"),
        ("associated_symptoms", "Other symptoms that occur together"),
        ("relevant_history", "Past conditions, surgeries, pregnancy status if applicable"),
        ("medications_and_allergies", "Current meds, supplements, and known allergies"),
        ("social_context", "Travel, sick contacts, work exposures, substance use if relevant"),
    ]
    missing: list[str] = []
    for key, label in optional_priority:
        val = (data.get(key) or "").strip()
        if len(val) < 3:
            missing.append(f"{key}: {label}")
    return missing


class IntakeAssessment(BaseModel):
    """Structured intake the agent fills from conversation."""

    chief_complaint: str = Field(default="", description="Primary symptom or concern")
    onset_and_course: str = Field(default="", description="Timing, progression, triggers")
    severity: str = Field(default="", description="Intensity or functional impact")
    associated_symptoms: str = Field(default="", description="Additional symptoms")
    demographics: str = Field(default="", description="Age group, sex, relevant context only if user shared")
    relevant_history: str = Field(default="", description="PMH, surgeries, OB/GYN if shared")
    medications_and_allergies: str = Field(default="", description="Meds and allergies if shared")
    social_context: str = Field(default="", description="Exposures, travel, contacts if shared")
    vital_signs_or_home_readings: str = Field(default="", description="Temp, BP, SpO2 if user reported")
    free_text_summary: str = Field(
        default="",
        description="Anything else material from the user (verbatim phrases help red-flag detection)",
    )


@mcp.tool()
async def get_intake_checklist() -> dict[str, Any]:
    """Return sections and example questions so the agent can systematically interview the user."""
    return {
        "disclaimer": DISCLAIMER,
        "goal": "Collect enough detail for a clinician; never pressure for unnecessary sensitive data.",
        "sections": [
            {
                "id": "opening",
                "prompts": [
                    "What is the main problem today?",
                    "When did it start, and did it come on suddenly or gradually?",
                    "On a 0–10 scale, how bad is it now?",
                    "What makes it better or worse?",
                ],
            },
            {
                "id": "associated",
                "prompts": [
                    "Any fever, chills, sweats?",
                    "Any cough, shortness of breath, chest discomfort?",
                    "Any nausea, vomiting, diarrhea, or abdominal pain?",
                    "Any headache, dizziness, weakness, numbness, vision changes?",
                    "Any urinary burning, frequency, or flank pain?",
                ],
            },
            {
                "id": "background",
                "prompts": [
                    "Do you have ongoing medical conditions?",
                    "What medications or supplements do you take?",
                    "Any known allergies (especially to medications)?",
                    "Could you be pregnant, or any recent travel or sick contacts?",
                ],
            },
            {
                "id": "safety",
                "prompts": [
                    "Do you feel safe right now? Any thoughts of harming yourself or others?",
                    "If symptoms suddenly worsen — trouble breathing, chest pain, confusion, severe bleeding — seek emergency care.",
                ],
            },
        ],
        "reminder": "Use record_intake_snapshot after each substantive reply to track completeness.",
    }


@mcp.tool()
async def record_intake_snapshot(
    chief_complaint: str = "",
    onset_and_course: str = "",
    severity: str = "",
    associated_symptoms: str = "",
    demographics: str = "",
    relevant_history: str = "",
    medications_and_allergies: str = "",
    social_context: str = "",
    vital_signs_or_home_readings: str = "",
    free_text_summary: str = "",
) -> dict[str, Any]:
    """Merge structured fields from the conversation; returns completeness hints for follow-up questions."""
    data = {
        "chief_complaint": chief_complaint,
        "onset_and_course": onset_and_course,
        "severity": severity,
        "associated_symptoms": associated_symptoms,
        "demographics": demographics,
        "relevant_history": relevant_history,
        "medications_and_allergies": medications_and_allergies,
        "social_context": social_context,
        "vital_signs_or_home_readings": vital_signs_or_home_readings,
        "free_text_summary": free_text_summary,
    }
    blob = _normalize(" ".join(data.values()))
    missing = _missing_fields(data)
    red = _red_flags(blob)
    return {
        "disclaimer": DISCLAIMER,
        "stored_fields": {k: v for k, v in data.items() if v.strip()},
        "completeness": {
            "missing_recommended": missing,
            "approximate_completeness_percent": max(0, min(100, 100 - min(len(missing) * 14, 100))),
        },
        "immediate_safety_screen": {
            "red_flag_alerts": red,
            "if_any_emergency_tier": "Stop further questioning and direct user to emergency services if appropriate.",
        },
    }


@mcp.tool()
async def screen_for_red_flags(
    narrative: str,
    vital_signs_or_home_readings: str = "",
) -> dict[str, Any]:
    """Fast pass over free text for emergency/urgent cues; use early in the conversation."""
    blob = _normalize(f"{narrative} {vital_signs_or_home_readings}")
    alerts = _red_flags(blob)
    return {
        "disclaimer": DISCLAIMER,
        "red_flag_alerts": alerts,
        "suggested_urgency_tier": _urgency_tier(alerts),
        "guidance": "If emergency tier, prioritize directing to in-person emergency care over detailed history.",
    }


@mcp.tool()
async def suggest_educational_differentials(
    chief_complaint: str,
    associated_symptoms: str = "",
    onset_and_course: str = "",
    demographics: str = "",
    free_text_summary: str = "",
) -> dict[str, Any]:
    """
    Non-exhaustive, keyword-based *educational* list of conditions that sometimes resemble the described pattern.
    Not diagnostic accuracy — for discussion with a clinician only.
    """
    blob = _normalize(
        f"{chief_complaint} {associated_symptoms} {onset_and_course} {demographics} {free_text_summary}"
    )
    alerts = _red_flags(blob)
    hints = _score_conditions(blob)
    return {
        "disclaimer": DISCLAIMER,
        "red_flag_alerts": alerts,
        "suggested_urgency_tier": _urgency_tier(alerts),
        "educational_possible_topics": hints if hints else [],
        "if_empty": "If no topics matched, the presentation may be non-specific — clinical evaluation is still appropriate if concerned.",
    }


@mcp.tool()
async def full_intake_assessment(intake_json: str) -> dict[str, Any]:
    """
    Parse JSON object with the same fields as record_intake_snapshot, then return completeness,
    red flags, educational topic hints, and suggested next steps (still not a diagnosis).
    """
    try:
        raw = json.loads(intake_json)
    except json.JSONDecodeError as e:
        return {"disclaimer": DISCLAIMER, "error": "invalid_json", "detail": str(e)}
    try:
        intake = IntakeAssessment.model_validate(raw)
    except Exception as e:
        return {"disclaimer": DISCLAIMER, "error": "validation_failed", "detail": str(e)}
    data = intake.model_dump()
    blob = _normalize(" ".join(str(v) for v in data.values()))
    missing = _missing_fields({k: str(v) for k, v in data.items()})
    alerts = _red_flags(blob)
    hints = _score_conditions(blob)
    tier = _urgency_tier(alerts)
    next_steps: list[str] = []
    if tier == "emergency":
        next_steps.append("Seek emergency in-person care now if symptoms are current or worsening.")
    elif tier == "urgent":
        next_steps.append("Same-day urgent clinic or telehealth is reasonable unless symptoms resolve quickly.")
    else:
        next_steps.append("If symptoms persist, worsen, or worry you, schedule routine or urgent outpatient care.")
    next_steps.append("Bring a written timeline, medication list, and any home readings to any visit.")
    return {
        "disclaimer": DISCLAIMER,
        "completeness": {
            "missing_recommended": missing,
            "approximate_completeness_percent": max(0, min(100, 100 - min(len(missing) * 14, 100))),
        },
        "red_flag_alerts": alerts,
        "suggested_urgency_tier": tier,
        "educational_possible_topics": hints,
        "suggested_next_steps": next_steps,
    }


if __name__ == "__main__":
    mcp.run(transport="stdio")
