# 2_lab2.py
# This is a cleaned version of the multi_model_evaluator.py file.
# It is a script that evaluates the performance of multiple models on a given question.
# Below is a cleaned multi_model_evaluator.py version you can save and run as a normal script.
#You can now:
#Create a file named multi_model_evaluator.py.
#Paste this code in.
#Ensure your .env has the needed keys (OPENAI_API_KEY, and others if you want those providers).
#Run with python multi_model_evaluator.py.


import os
import time
from anthropic import Anthropic
from dotenv import load_dotenv
from openai import OpenAI

# =========================
# Environment setup
# =========================

#load_dotenv()
load_dotenv(override=True)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
GEMINI_API_KEY = os.getenv("GOOGLE_API_KEY")
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL")
#   OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

if not OPENAI_API_KEY:
    raise RuntimeError("OPENAI_API_KEY is required in your .env file.")

# Base OpenAI client (for OpenAI-hosted models, including oss models)
openai_client = OpenAI(api_key=OPENAI_API_KEY)

# =========================
# Helper: call different providers
# =========================

def _extract_text(response, provider: str) -> str:
    """
    Defensive helper that pulls the first text chunk out of a Responses API
    payload. Some providers return tool calls or non-text chunks, so we fall
    back to output_text (if available) before giving up.
    """
    # Try the structured Responses API shape first
    output = getattr(response, "output", None) or []
    for item in output:
        content_items = getattr(item, "content", None) or []
        for content in content_items:
            text = getattr(content, "text", None)
            if text:
                # text may come through as list[str]
                if isinstance(text, list):
                    return "".join(text)
                return text

    # Fall back to the convenience output_text field if present
    output_text = getattr(response, "output_text", None)
    if output_text:
        if isinstance(output_text, list):
            return output_text[0]
        return output_text

    return f"{provider} response did not include text content."


def call_openai_model(model: str, prompt: str) -> str:
    response = openai_client.responses.create(
        model=model,
        input=prompt,
    )
    return _extract_text(response, "openai")


def call_anthropic_model(model: str, prompt: str) -> str:
    if not ANTHROPIC_API_KEY:
        return "ANTHROPIC_API_KEY missing; cannot call Anthropic."

    # client = OpenAI(
    #     api_key=ANTHROPIC_API_KEY,
    #     base_url="https://api.anthropic.com/v1"
    # )
    # response = client.responses.create(
    #     model=model,
    #     input=prompt,
    # )

    client = Anthropic(api_key=ANTHROPIC_API_KEY)
    response = client.messages.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=4096,
    )
    return response.content[0].text

def call_gemini_model(model: str, prompt: str) -> str:
    if not GEMINI_API_KEY:
        return "GEMINI_API_KEY missing; cannot call Gemini."
    client = OpenAI(
        api_key=GEMINI_API_KEY,
        base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
    )
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.choices[0].message.content


def call_deepseek_model(model: str, prompt: str) -> str:
    if not DEEPSEEK_API_KEY:
        return "DEEPSEEK_API_KEY missing; cannot call DeepSeek."
    client = OpenAI(
        api_key=DEEPSEEK_API_KEY,
        base_url="https://api.deepseek.com/v1"
    )
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.choices[0].message.content


def call_groq_model(model: str, prompt: str) -> str:
    if not GROQ_API_KEY:
        return "GROQ_API_KEY missing; cannot call Groq."
    client = OpenAI(
        api_key=GROQ_API_KEY,
        base_url="https://api.groq.com/openai/v1"
    )
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.choices[0].message.content


def call_ollama_model(model: str, prompt: str) -> str:
    """
    Expects OLLAMA_BASE_URL to point to an Ollama server exposing an OpenAI-compatible /v1 API.
    If not set up, this will return a message instead of failing hard.
    """
    if not OLLAMA_BASE_URL:
        return "OLLAMA_BASE_URL missing; cannot call Ollama."
    try:
        client = OpenAI(
            base_url=f"{OLLAMA_BASE_URL}",
            api_key="ollama"  # dummy token; Ollama usually ignores this
        )
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Ollama call failed: {e}"


# =========================
# Step 1: generate a single hard question
# =========================

QUESTION_GENERATOR_MODEL = "gpt-4.1-mini"   # or any OpenAI model you prefer

GENERATOR_SYSTEM_PROMPT = (
    "You are a question generation expert. "
    "Generate one challenging, real-world question that will test multiple LLMs. "
    "Make it complex enough that different LLMs might give different, nuanced answers. "
    "Output only the question text, nothing else."
)

def generate_challenge_question() -> str:
    response = openai_client.responses.create(
        model=QUESTION_GENERATOR_MODEL,
        input=[
            {
                "role": "system",
                "content": GENERATOR_SYSTEM_PROMPT,
            }
        ],
    )
    question = response.output[0].content[0].text.strip()
    return question


# =========================
# Step 2: define competitor models
# =========================

# Adjust or comment out entries depending on which APIs/keys you actually have.
# For now, we only enable the OpenAI model that you already have working.
COMPETITORS = [
    {
        "name": "Claude sonnet",
        "provider": "anthropic",
        "model": "claude-sonnet-4-5",
    },
    {
        "name": "OpenAI gpt-5-nano",
        "provider": "openai",
        "model": "gpt-5-nano",
    },
    {
        "name": "Gemini 2.0-flash",
        "provider": "gemini",
        "model": "gemini-2.0-flash",
    },
    {
        "name": "Local llama3.2 via Ollama",
        "provider": "ollama",
        "model": "llama3.2",
    },
        {
        "name": "DeepSeek Chat",
        "provider": "deepseek",
        "model": "deepseek-chat",
    },
        {
        "name": "GROQ openai/gpt-oss-120b",
        "provider": "groq",
        "model": "openai/gpt-oss-120b",
    },
]

def call_competitor(provider: str, model: str, prompt: str) -> str:
    if provider == "openai":
        return call_openai_model(model, prompt)
    elif provider == "anthropic":
        return call_anthropic_model(model, prompt)
    elif provider == "gemini":
        return call_gemini_model(model, prompt)
    elif provider == "deepseek":
        return call_deepseek_model(model, prompt)
    elif provider == "groq":
        return call_groq_model(model, prompt)
    elif provider == "ollama":
        return call_ollama_model(model, prompt)
    else:
        return f"Unknown provider: {provider}"


# =========================
# Step 3: ask all competitors the same question
# =========================
  
def collect_competitor_answers(question: str):
    all_answers = []
    for idx, competitor in enumerate(COMPETITORS, start=1):
        name = competitor["name"]
        provider = competitor["provider"]
        model = competitor["model"]

        print(f"\n=== Asking competitor {idx}: {name} ===")
        start = time.time()
        answer = call_competitor(provider, model, question)
        elapsed = time.time() - start

        print(f"Answer from {name} (took {elapsed:.2f}s):\n")
        print(answer)
        print("\n" + "=" * 60 + "\n")

        all_answers.append(
            {
                "index": idx,
                "name": name,
                "provider": provider,
                "model": model,
                "answer": answer,
                "elapsed_seconds": elapsed,
            }
        )
    return all_answers


# =========================
# Step 4: create judge prompt with all answers
# =========================

def build_judge_prompt(question: str, responses: list) -> str:
    pieces = []
    pieces.append(
        "You are an expert judge comparing responses from multiple AI models to the same question.\n"
        "You will receive:\n"
        "1) The question.\n"
        "2) Several numbered responses from different competitors.\n\n"
        "Your task:\n"
        "- Carefully read each response.\n"
        "- Consider correctness, depth, clarity, helpfulness, and reasoning.\n"
        "- Produce a strict ranking from best to worst.\n\n"
        "Output format:\n"
        "Return ONLY valid JSON with this exact schema (no backticks, no explanation):\n"
        "{\n"
        '  \"rankings\": [\n'
        '    {\"competitor_index\": <number>, \"score\": <number from 0 to 10>, \"justification\": \"<short text>\"}\n'
        "  ]\n"
        "}\n"
        "The first element in rankings must be the best answer (highest score), then next best, etc.\n\n"
        "Here is the question:\n"
    )
    pieces.append(question)
    pieces.append("\n\nNow here are the competitor responses:\n")

    for r in responses:
        pieces.append(f"\n=== Response from competitor {r['index']} ({r['name']}) ===\n")
        pieces.append(r["answer"])
        pieces.append("\n")

    return "".join(pieces)


# =========================
# Step 5: ask a judge model to rank them
# =========================

JUDGE_MODEL = "o3-mini"   # or any OpenAI model suitable for judging

def judge_responses(question: str, responses: list):
    judge_prompt = build_judge_prompt(question, responses)

    response = openai_client.responses.create(
        model=JUDGE_MODEL,
        input=judge_prompt,
    )

    # Fallback: get plain-text output and parse JSON ourselves
    import json

    raw_text = _extract_text(response, "openai")
    result = json.loads(raw_text)
    return result


def print_rankings(judge_result, responses):
    index_to_response = {r["index"]: r for r in responses}

    print("\n=== Final Rankings ===\n")
    for rank, entry in enumerate(judge_result["rankings"], start=1):
        idx = entry["competitor_index"]
        score = entry["score"]
        justification = entry["justification"]
        competitor = index_to_response.get(idx, {})
        name = competitor.get("name", f"Unknown (index {idx})")

        print(f"Rank {rank}: {name}")
        print(f"  Score: {score}")
        print(f"  Justification: {justification}")
        print()


# =========================
# Main entry point
# =========================

def main():
    print("Generating a single challenging question...\n")
    question = generate_challenge_question()
    print("Question:\n")
    print(question)
    print("\n" + "=" * 60 + "\n")

    print("Collecting competitor answers...\n")
    responses = collect_competitor_answers(question)

    print("Asking judge model for rankings...\n")
    judge_result = judge_responses(question, responses)

    print_rankings(judge_result, responses)


if __name__ == "__main__":
    main()
