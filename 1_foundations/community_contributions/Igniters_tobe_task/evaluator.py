"""
Bio Agent — Evaluator (LLM-as-Judge)
--------------------------------------
Scores agent responses using a separate Ollama model.
Returns structured feedback for the reflection loop.
"""

import json

from openai import OpenAI

from config import OLLAMA_BASE_URL, OLLAMA_API_KEY, EVALUATOR_MODEL


# ── Evaluator Client ──────────────────────────────────────────────────

_client = OpenAI(base_url=OLLAMA_BASE_URL, api_key=OLLAMA_API_KEY)

EVAL_SYSTEM_PROMPT = """You are a strict quality evaluator for a professional career assistant chatbot.

Your job is to score each response the assistant gives. You will receive:
- The user's original question
- The assistant's response
- Context from the knowledge base (if any was used)

Score the response on a 1-10 scale based on THREE criteria:
1. **Accuracy**: Does it match the factual information from the knowledge base?
2. **Professionalism**: Is the tone appropriate for representing someone professionally?
3. **Completeness**: Does it fully answer the question?

You MUST respond with ONLY valid JSON in this exact format, nothing else:
{"score": <integer 1-10>, "feedback": "<specific improvement suggestions>"}

If the response is excellent, still provide the JSON with positive feedback."""


def evaluate_response(
    user_question: str,
    agent_answer: str,
    context: str = "",
) -> dict:
    """
    Score an agent response using the evaluator model.

    Returns:
        dict with keys "score" (int) and "feedback" (str).
        On failure, returns {"score": 7, "feedback": "Evaluation failed, accepting response."}.
    """
    eval_prompt = f"""## User Question
{user_question}

## Assistant's Response
{agent_answer}
"""
    if context:
        eval_prompt += f"""
## Knowledge Base Context Used
{context}
"""

    # Try up to 2 times to get valid JSON from the evaluator
    for attempt in range(2):
        try:
            response = _client.chat.completions.create(
                model=EVALUATOR_MODEL,
                messages=[
                    {"role": "system", "content": EVAL_SYSTEM_PROMPT},
                    {"role": "user", "content": eval_prompt},
                ],
                temperature=0.1,  # Low temp for consistent scoring
            )

            raw = response.choices[0].message.content.strip()

            # Handle cases where model wraps JSON in markdown code blocks
            if raw.startswith("```"):
                raw = raw.split("\n", 1)[1] if "\n" in raw else raw[3:]
                raw = raw.rsplit("```", 1)[0].strip()

            result = json.loads(raw)

            # Validate structure
            score = int(result.get("score", 7))
            score = max(1, min(10, score))  # clamp to 1-10
            feedback = str(result.get("feedback", "No feedback provided."))

            return {"score": score, "feedback": feedback}

        except (json.JSONDecodeError, ValueError, KeyError):
            if attempt == 0:
                continue  # retry once

    # Fallback: if we can't parse evaluator output, accept the response
    return {"score": 7, "feedback": "Evaluation parsing failed; accepting response."}
