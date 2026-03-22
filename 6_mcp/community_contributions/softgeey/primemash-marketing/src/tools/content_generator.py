"""
Content generation tools powered by OpenRouter.
Nigerian-market focused, culturally authentic, high engagement.
"""

import os
import json
import httpx
from datetime import datetime
from openai import OpenAI
from dotenv import load_dotenv
from src.lib.brand_context import BRAND_CONTEXT, PLATFORM_GUIDELINES, CONTENT_CALENDAR

load_dotenv()


def _get_openrouter_client() -> OpenAI:
    return OpenAI(
        api_key=os.environ["OPENROUTER_API_KEY"],
        base_url=os.environ.get("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"),
        default_headers={
            "HTTP-Referer": "https://primemash.com",
            "X-Title": "Primemash Marketing Agent",
        },
    )


def _call_llm(system_prompt: str, user_prompt: str, temperature: float = 0.85) -> str:
    client = _get_openrouter_client()
    model  = os.environ.get("OPENROUTER_MODEL", "anthropic/claude-3.5-sonnet")
    response = client.chat.completions.create(
        model=model,
        temperature=temperature,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": user_prompt},
        ],
    )
    return response.choices[0].message.content.strip()


# ── Nigerian content style guide injected into every prompt ───────────────────

NIGERIAN_STYLE = """
NIGERIAN CONTENT STYLE — follow these rules exactly:

TONE & VOICE:
- Write like a sharp, successful Lagos entrepreneur talking to peers
- Confident, direct, no corporate fluff — Nigerians respect substance
- Use "you" and "your business" to make it personal
- Occasional Pidgin phrases add authenticity: "e no easy", "the thing do", "sharp sharp", "story for another day"
- Reference real Nigerian business pain points: NEPA/generator costs, bank charges, slow payment cycles, staff on multiple WhatsApp groups, manual Excel invoicing, chasing clients for payment

SPECIFICITY (this is critical):
- Use Naira figures: ₦50,000/month, ₦2.3M saved, not "significant savings"
- Use real time figures: "saving 23 hours a week", not "saving time"
- Reference real Nigerian tools businesses use: Paystack, Flutterwave, Zoho, WhatsApp Business, GTBank, Access Bank
- Mention real industries: Lagos real estate agents, Abuja consultants, PH oil & gas suppliers, Lagos e-commerce brands

ORIGINALITY:
- Never start with "In today's fast-paced world" or any generic opener
- Never use "game-changer", "leverage", "synergy", "holistic approach"
- Open with a specific scenario, a provocative question, or a Naira figure
- Tell a micro-story: set up a relatable problem, then reveal the solution

STRUCTURE FOR LINKEDIN:
- Line 1: Hook — specific number, bold claim, or relatable scenario (this is what shows before "see more")
- Lines 2-4: The problem (make them feel seen)
- Lines 5-8: The insight/solution (specific, practical)
- Lines 9-10: The result/CTA
- End with 3-5 hashtags on their own line
"""


# ── Content generation functions ──────────────────────────────────────────────

def generate_linkedin_post(content_type: str, topic: str = None) -> str:
    """Generate a high-quality, culturally authentic LinkedIn post."""

    day          = datetime.now().strftime("%A").lower()
    default_type = CONTENT_CALENDAR.get(day, "educational")
    content_type = content_type or default_type

    system_prompt = f"""You are the content strategist for Primemash Technologies, writing for Nigerian business owners on LinkedIn.

{BRAND_CONTEXT}

{NIGERIAN_STYLE}

LINKEDIN SPECIFICS:
- Max 1,300 characters for best reach (can go to 3,000 but shorter performs better)
- Use line breaks generously — white space increases readability
- 3-5 hashtags at the end: mix Primemash-specific and broad Nigerian business tags
- No bold markdown (**text**) — LinkedIn doesn't render it in all views

Return ONLY the post text. No explanation, no preamble."""

    content_examples = {
        "case_study": "A specific Nigerian business (name the industry, city, problem, exact savings in ₦ and hours)",
        "educational": "A practical how-to that a Lagos SME owner can use tomorrow morning",
        "thought_leadership": "A contrarian take on automation/business in Nigeria backed by a specific observation",
        "social_proof": "A client win with specific metrics — ₦ saved, hours freed, revenue gained",
        "product_showcase": "Show one specific Primemash feature solving a named Nigerian business problem",
        "motivation_and_tips": "Monday energy — a specific actionable tip for Nigerian entrepreneurs",
        "behind_scenes": "Behind the scenes of building Primemash — real, raw, relatable",
        "engagement": "A question that makes Nigerian business owners stop and think",
    }

    example = content_examples.get(content_type, "practical business automation insight")

    user_prompt = f"""Write a LinkedIn post for Primemash Technologies.

Content type: {content_type}
Focus: {example}
Specific topic: {topic or "choose the most relevant Nigerian business automation topic for today"}

The post must feel like it was written by a sharp Lagos entrepreneur, not a marketing team.
Use at least one specific Naira figure or time saving metric.
Reference a real Nigerian business scenario.
Return only the post text."""

    return _call_llm(system_prompt, user_prompt)


def generate_twitter_post(content_type: str, topic: str = None) -> str:
    """Generate a punchy, culturally authentic tweet."""

    system_prompt = f"""You are the Twitter voice for Primemash Technologies — sharp, Nigerian, no fluff.

{BRAND_CONTEXT}

{NIGERIAN_STYLE}

TWITTER RULES:
- HARD LIMIT: 270 characters maximum (leave room for hashtags)
- One single idea — no trying to say everything
- Nigerian entrepreneurs scroll fast — the first 5 words must stop them
- Max 2 hashtags
- No "Thread 🧵" unless it's actually a thread

Return ONLY the tweet text. Nothing else."""

    user_prompt = f"""Write a tweet for Primemash.
Type: {content_type}
Topic: {topic or "automation tip for Nigerian businesses"}

Under 270 characters. Punchy. Nigerian. Real.
Return only the tweet."""

    content = _call_llm(system_prompt, user_prompt)
    if len(content) > 280:
        content = content[:277] + "..."
    return content


def generate_instagram_caption(content_type: str, topic: str = None) -> str:
    """Generate an Instagram caption with Nigerian cultural authenticity."""

    system_prompt = f"""You are the Instagram content creator for Primemash Technologies.

{BRAND_CONTEXT}

{NIGERIAN_STYLE}

INSTAGRAM RULES:
- First line must grab attention BEFORE the "more" cutoff (no hashtags in first line)
- Short punchy paragraphs — 2-3 lines each
- Emojis welcome but not every sentence
- CTA: save this, share with a business owner you know, DM us "automate"
- 12-15 hashtags at the very end after a line break

Return ONLY the caption text."""

    user_prompt = f"""Write an Instagram caption for Primemash.
Type: {content_type}
Topic: {topic or "business automation results for Nigerian SMEs"}

First line must hook. Nigerian tone. Real metrics.
Return only the caption."""

    return _call_llm(system_prompt, user_prompt)


def generate_campaign_content_plan(
    campaign_name: str,
    objective: str,
    platforms: list,
    duration_days: int,
) -> dict:
    """Generate a full campaign content calendar."""

    system_prompt = f"""You are the head of marketing for Primemash Technologies.

{BRAND_CONTEXT}

{NIGERIAN_STYLE}

Return valid JSON only. No markdown, no explanation."""

    user_prompt = f"""Create a {duration_days}-day content plan.

Campaign: {campaign_name}
Objective: {objective}
Platforms: {", ".join(platforms)}
Frequency: 3 posts per week per platform

Return JSON:
{{
  "campaign_name": "...",
  "objective": "...",
  "duration_days": {duration_days},
  "posts": [
    {{
      "day": 1,
      "platform": "linkedin",
      "content_type": "educational",
      "topic": "specific Nigerian business topic",
      "hook": "specific opening line idea with Naira figure or scenario"
    }}
  ]
}}"""

    raw = _call_llm(system_prompt, user_prompt, temperature=0.6)
    raw = raw.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    try:
        return json.loads(raw.strip())
    except json.JSONDecodeError:
        return {
            "campaign_name": campaign_name,
            "objective": objective,
            "duration_days": duration_days,
            "posts": [],
            "error": "Failed to parse plan",
            "raw": raw,
        }


# ── Image fetching via Unsplash ──────────────────────────────────────────────

def fetch_post_image(post_content: str, platform: str = "linkedin") -> str:
    """
    Fetch a relevant image URL from Unsplash based on post content.
    Returns a direct image URL or empty string if unavailable.

    Requires UNSPLASH_ACCESS_KEY in .env
    Get a free key at: unsplash.com/developers
    Only the Access Key is needed — Secret Key is not used.
    """
    access_key = os.environ.get("UNSPLASH_ACCESS_KEY", "")
    if not access_key:
        return ""

    keywords = _extract_image_keywords(post_content)

    try:
        with httpx.Client(timeout=10) as client:
            r = client.get(
                "https://api.unsplash.com/search/photos",
                headers={"Authorization": f"Client-ID {access_key}"},
                params={
                    "query":          keywords,
                    "per_page":       5,
                    "orientation":    "landscape",
                    "content_filter": "high",
                },
            )
        if r.status_code != 200:
            return ""

        results = r.json().get("results", [])
        if not results:
            return _fetch_fallback_image(access_key)

        return results[0]["urls"]["regular"]

    except Exception:
        return ""


def _fetch_fallback_image(access_key: str) -> str:
    """Fetch a generic African business image as fallback."""
    try:
        with httpx.Client(timeout=10) as client:
            r = client.get(
                "https://api.unsplash.com/search/photos",
                headers={"Authorization": f"Client-ID {access_key}"},
                params={
                    "query":       "african business entrepreneur",
                    "per_page":    3,
                    "orientation": "landscape",
                },
            )
        results = r.json().get("results", [])
        return results[0]["urls"]["regular"] if results else ""
    except Exception:
        return ""


def _extract_image_keywords(content: str) -> str:
    """Map post content to relevant Unsplash search keywords."""
    content_lower = content.lower()

    if any(w in content_lower for w in ["invoice", "payment", "finance", "accounting"]):
        return "african business finance office"
    if any(w in content_lower for w in ["whatsapp", "customer", "chat", "message"]):
        return "african entrepreneur smartphone business"
    if any(w in content_lower for w in ["inventory", "stock", "warehouse", "retail"]):
        return "african retail business store"
    if any(w in content_lower for w in ["real estate", "property", "agent", "listing"]):
        return "african real estate business"
    if any(w in content_lower for w in ["hr", "payroll", "staff", "employee", "team"]):
        return "african business team meeting"
    if any(w in content_lower for w in ["crm", "sales", "lead", "pipeline", "revenue"]):
        return "african sales business success"
    if any(w in content_lower for w in ["ecommerce", "online", "shopify", "order"]):
        return "african ecommerce business laptop"
    if any(w in content_lower for w in ["automat", "workflow", "process", "system"]):
        return "african business technology automation"

    return "african business entrepreneur success"


def generate_image_prompt(content_type: str, topic: str, platform: str) -> str:
    """Generate an image description prompt for AI image generation."""
    system_prompt = "You are a visual director. Return only a concise image description under 80 words."
    user_prompt = f"""Image for a {platform} post.
Content type: {content_type}
Topic: {topic}
Brand: Primemash Technologies (business automation, Nigerian market)
Style: Professional, modern, African business context.
Avoid: stock photo clichés, generic handshakes, suits in empty offices."""
    return _call_llm(system_prompt, user_prompt, temperature=0.5)
