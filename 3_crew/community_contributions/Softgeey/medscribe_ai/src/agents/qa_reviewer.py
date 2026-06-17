"""
QA Reviewer Agent
Responsibility: Review the discharge summary for completeness, clinical accuracy,
and compliance with documentation standards. Flag issues and produce final approval.
"""

from src.utils.llm_client import call_llm

SYSTEM_PROMPT = """You are a Chief Medical Officer and clinical documentation auditor.
Your role is to review a hospital discharge summary for quality and safety.

Evaluate the summary against these criteria:
1. All required sections are present and non-empty
2. Medications include dose, frequency, and duration
3. Follow-up appointments are specific (specialist named, timeframe given)
4. Return-to-ER criteria are clearly listed
5. No contradictions between diagnoses and medications
6. Patient education points are actionable
7. Language is professional and unambiguous

Output a JSON review report:
{
  "approved": true | false,
  "quality_score": 0-100,
  "issues_found": [],
  "recommendations": [],
  "compliant_sections": [],
  "missing_or_incomplete_sections": [],
  "reviewer_note": ""
}

Be rigorous. Patient safety depends on this review.
Output ONLY valid JSON — no prose, no markdown fences.
"""


def run(discharge_summary: str) -> str:
    """
    Review a discharge summary and return a JSON quality report.
    """
    return call_llm(
        system_prompt=SYSTEM_PROMPT,
        user_prompt=f"Review this discharge summary:\n\n{discharge_summary}",
        temperature=0.1,
    )
