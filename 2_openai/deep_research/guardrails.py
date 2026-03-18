
import os
import re
from dataclasses import dataclass
from openai import OpenAI

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
MAX_QUERY_LENGTH = 2000
MAX_TOTAL_INPUT_LENGTH = 8000
SENSITIVE_TOPICS_DEFAULT = [
    "specific medical diagnosis or treatment",
    "legal advice for a specific case",
    "financial advice for specific investments",
]

# PII patterns (simple; extend as needed)
EMAIL_PATTERN = re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+")
PHONE_PATTERN = re.compile(r"\+?\d{1,3}[-.\s]?\(?\d{2,4}\)?[-.\s]?\d{2,4}[-.\s]?\d{2,4}[-.\s]?\d{2,4}\b")
# UK-style postcode
POSTCODE_PATTERN = re.compile(r"[A-Z]{1,2}\d[A-Z\d]?\s*\d[A-Z]{2}", re.IGNORECASE)


@dataclass
class GuardrailResult:
    passed: bool
    message: str


def _check_length(query: str, answers: list[str] | None) -> GuardrailResult | None:
    total = len(query or "")
    for a in answers or []:
        total += len(a or "")
    if total > MAX_TOTAL_INPUT_LENGTH:
        return GuardrailResult(
            False,
            f"Input is too long (max {MAX_TOTAL_INPUT_LENGTH} characters). Please shorten your query or answers.",
        )
    if len((query or "").strip()) > MAX_QUERY_LENGTH:
        return GuardrailResult(
            False,
            f"Research topic is too long (max {MAX_QUERY_LENGTH} characters). Please shorten it.",
        )
    return None


def _check_pii(text: str) -> list[str]:
    found = []
    for m in EMAIL_PATTERN.finditer(text):
        found.append(f"Email: {m.group()}")
    for m in PHONE_PATTERN.finditer(text):
        found.append(f"Phone: {m.group()}")
    for m in POSTCODE_PATTERN.finditer(text):
        found.append(f"Postcode: {m.group()}")
    return found


def _check_topic_intent(client: OpenAI, query: str, model: str = "gpt-4o-mini") -> GuardrailResult:
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": """You are a guardrail. Decide if the user input is a genuine research request suitable for a deep research agent.
Reply with exactly this JSON and nothing else: {"valid": true} or {"valid": false, "reason": "short reason"}.
Reject: empty input, pure gibberish, jokes, requests to write code/poems/stories, or clearly off-topic. Accept: any reasonable request to research a topic.""",
                },
                {"role": "user", "content": (query or "").strip()[:1500]},
            ],
            max_tokens=150,
        )
        content = (response.choices[0].message.content or "").strip()
        if "valid\": true" in content or '"valid":true' in content:
            return GuardrailResult(True, "")
        import json
        try:
            d = json.loads(content)
            reason = d.get("reason", "Not a valid research request.")
            return GuardrailResult(False, f"Query rejected: {reason}")
        except Exception:
            return GuardrailResult(False, "Query rejected: Could not verify as a research request.")
    except Exception as e:
        return GuardrailResult(False, f"Guardrail check failed: {e}")


def run_guardrails(
    query: str,
    answers: list[str] | None = None,
    *,
    intent_query: str | None = None,
    check_pii: bool = True,
    check_intent: bool = True,
    check_length: bool = True,
    sensitive_topics: list[str] | None = None,
    openai_api_key: str | None = None,
    allow_recipient_email: bool = False,
) -> GuardrailResult:
   
    query = (query or "").strip()
    answers = answers or []
    topic_for_intent = (intent_query or query).strip()

    if check_length:
        r = _check_length(query, answers)
        if r is not None:
            return r

    if not topic_for_intent:
        return GuardrailResult(False, "Please enter a research topic.")

    if check_pii:
        full = query + " " + " ".join(answers or [])
        if allow_recipient_email:
            # Allow a single 'Recipient email: someone@example.com' line without failing PII checks.
            full = re.sub(
                r"Recipient email:\s*[^\s]+",
                "Recipient email: [redacted]",
                full,
                flags=re.IGNORECASE,
            )
        pii = _check_pii(full)
        if pii:
            return GuardrailResult(
                False,
                "Personal data detected (e.g. email, phone, postcode). Remove it before researching. "
                f"Found: {', '.join(pii[:5])}{'...' if len(pii) > 5 else ''}",
            )

    if check_intent:
        api_key = openai_api_key or os.environ.get("OPENAI_API_KEY")
        if api_key:
            client = OpenAI(api_key=api_key)
            r = _check_topic_intent(client, topic_for_intent)
            if not r.passed:
                return r
        # If no API key, skip intent check

    return GuardrailResult(True, "")
