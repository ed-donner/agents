"""Deterministic local tools used by BudgetBuy agents."""

from __future__ import annotations

import os
from typing import Any

import resend
from chump import Application
from agents import function_tool
from agents import input_guardrail, GuardrailFunctionOutput, Agent, TResponseInputItem, RunResult, Runner
from utils import extract_last_user_text
from schemas import GadgetScopeCheck
import requests

@input_guardrail
async def enforce_gadget_only(
    ctx,
    agent: Agent,
    message: list[TResponseInputItem],
) -> GuardrailFunctionOutput:
    last_user_message = extract_last_user_text(message)
    if not last_user_message.strip():
        return GuardrailFunctionOutput(tripwire_triggered=False, output_info={"scope_check": {"is_gadget_request": False, "message": "No user message"}})

    result: RunResult = await Runner.run(
        gadget_guardrail_agent,
        last_user_message,
        context=ctx.context,
    )
    assert isinstance(result.final_output, GadgetScopeCheck)
    blocked = not result.final_output.is_gadget_request
    return GuardrailFunctionOutput(
        tripwire_triggered=blocked,
        output_info={"scope_check": result.final_output.model_dump()},
    )

def score_products(
    products: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Score products with a deterministic generic ranking."""
    if not products:
        return []

    # Fixed, generic weights: affordability first, then warranty and availability.
    weights = {"price": 0.6, "warranty": 0.25, "availability": 0.15}

    max_warranty = max(float(p.get("warranty_months", 0.0)) for p in products) or 1.0
    max_price = max(float(p.get("price_ngn", 0.0)) for p in products) or 1.0

    ranked: list[dict[str, Any]] = []
    for p in products:
        warranty_score = float(p.get("warranty_months", 0.0)) / max_warranty
        price_score = 1.0 - (float(p.get("price_ngn", 0.0)) / max_price)
        availability_raw = str(p.get("availability", "unknown")).lower()
        if "in_stock" in availability_raw:
            availability_score = 1.0
        elif "limited" in availability_raw:
            availability_score = 0.5
        else:
            availability_score = 0.0
        score = (
            price_score * weights["price"]
            + warranty_score * weights["warranty"]
            + availability_score * weights["availability"]
        )
        ranked.append({"product": p, "score": round(score, 4)})

    ranked.sort(key=lambda item: item["score"], reverse=True)
    return ranked


@function_tool
def send_email(to: str, subject: str, body: str) -> str:
    """Send email via Resend SDK."""
    recipient = to.strip()
    if not recipient:
        return "Email skipped: no recipient provided."

    api_key = os.environ.get("RESEND_API_KEY", "").strip()
    from_email = os.environ.get("RESEND_FROM_EMAIL", "").strip()
    if not api_key:
        return "Email skipped: RESEND_API_KEY is not set."
    if not from_email:
        return "Email skipped: RESEND_FROM_EMAIL is not set."

    resend.api_key = api_key
    try:
        response = resend.Emails.send(
            {
                "from": from_email,
                "to": [recipient],
                "subject": subject.strip() or "BudgetBuy update",
                "text": body.strip() or "BudgetBuy shortlist update.",
            }
        )
    except Exception as exc:
        return f"Email failed: {exc.__class__.__name__}."

    response_id = ""
    if isinstance(response, dict):
        response_id = str(response.get("id", "")).strip()
    if response_id:
        return f"Email sent to {recipient} (id: {response_id})."
    return f"Email sent to {recipient}."


@function_tool
def send_push(title: str, message: str) -> str:
    """Send push notification via Pushover client library."""
    if not message.strip():
        return "Push skipped: empty message."

    app_token = os.environ.get("PUSHOVER_TOKEN", "").strip()
    user_key = os.environ.get("PUSHOVER_USER", "").strip()
    if not app_token or not user_key:
        return "Push skipped: set PUSHOVER_TOKEN and PUSHOVER_USER."

    try:
        pushover_url = "https://api.pushover.net/1/messages.json"
        payload = {"user": user_key, "token": app_token, "message": message}
        requests.post(pushover_url, data=payload)
        return "Push sent."
    except Exception as exc:
        return f"Push failed: {exc.__class__.__name__}."
