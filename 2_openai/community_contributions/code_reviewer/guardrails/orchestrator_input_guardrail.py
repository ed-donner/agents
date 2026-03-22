from agents import Agent, input_guardrail, GuardrailFunctionOutput, RunContextWrapper
from openai import AsyncOpenAI
from models import UserInputAnalysis
import os
import json


client = AsyncOpenAI(
    base_url=os.environ.get("OPENROUTER_BASE_URL"),
    api_key=os.environ.get("OPENROUTER_API_KEY"),
)


@input_guardrail
async def validate_user_input(
    ctx: RunContextWrapper, agent: Agent, input
) -> GuardrailFunctionOutput:
    """
    Only blocks input when a GitHub URL or local path is detected but fails validation.
    Plain conversational input is always allowed through.
    """

    # ── Step 1: Extract plain text ─────────────────────────────────────────────
    if isinstance(input, str):
        raw_text = input
    elif isinstance(input, list):
        raw_text = " ".join(
            msg.get("content", "") if isinstance(msg, dict) else str(msg)
            for msg in input
        )
    else:
        raw_text = str(input)

    raw_text = raw_text.strip()

    # ── Step 2: LLM extraction ─────────────────────────────────────────────────
    system_prompt = """
You are an input analyzer for a code review system.
Your job is to detect whether the user input contains a GitHub URL or a local
file system path. Extract it if present.

Respond ONLY with valid JSON in this exact structure:
{
  "has_repo_reference": <true|false>,
  "extracted_value": "<the extracted URL or path, or empty string if none>",
  "input_type": "<github_url | local_path | none>",
  "reason": "<one sentence explanation>"
}

Rules:
- Set has_repo_reference to true ONLY if a URL or file path is explicitly present
- A GitHub URL must start with https://github.com
- A local path looks like C:\\folder\\repo or /home/user/repo or ./myrepo
- Conversational messages like "hello", "help me", "what can you do" have
  has_repo_reference=false and input_type="none"
- Return only JSON, no markdown, no preamble
"""

    try:
        response = await client.chat.completions.parse(
            model=os.environ.get("GPT_MODEL"),
            max_tokens=256,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": raw_text}
            ],
            response_format=UserInputAnalysis,
        )

        parsed = response.choices[0].message.parsed

    except Exception as e:
        print(f"[GUARDRAIL ERROR] LLM check failed: {str(e)}, allowing input through")
        return GuardrailFunctionOutput(
            output_info="Guardrail check unavailable, passing input through.",
            tripwire_triggered=False
        )

    # ── Step 3: Apply validation only when a reference was detected ────────────

    # No URL or path in input — plain conversation, always allow through
    if not parsed.has_repo_reference:
        return GuardrailFunctionOutput(
            output_info="No repo reference detected. Passing conversational input through.",
            tripwire_triggered=False
        )

    extracted = parsed.extracted_value.strip()

    # GitHub URL detected — validate it
    if parsed.input_type == "github_url":
        is_valid = extracted.startswith("https://github.com")
        return GuardrailFunctionOutput(
            output_info=(
                f"GitHub URL {'accepted' if is_valid else 'rejected — must start with https://github.com'}: "
                f"'{extracted}'"
            ),
            tripwire_triggered=not is_valid
        )

    # Local path detected — validate it exists on disk
    if parsed.input_type == "local_path":
        path_exists = os.path.exists(extracted)
        return GuardrailFunctionOutput(
            output_info=(
                f"Local path {'found' if path_exists else 'not found on disk'}: "
                f"'{extracted}'"
            ),
            tripwire_triggered=not path_exists
        )

    # Fallback — unrecognised type, allow through
    return GuardrailFunctionOutput(
        output_info=f"Unrecognised input type '{parsed.input_type}', passing through.",
        tripwire_triggered=False
    )