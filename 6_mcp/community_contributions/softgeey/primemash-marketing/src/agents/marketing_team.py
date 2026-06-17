"""
Primemash Marketing Agent
Single-agent architecture — all tools attached directly.
No handoffs, no delegation loops, just execution.
"""

import os
import json
from datetime import datetime
from dotenv import load_dotenv

from agents import Agent, Runner, function_tool, set_tracing_disabled
from agents.models.openai_chatcompletions import OpenAIChatCompletionsModel
from openai import AsyncOpenAI

from src.lib.brand_context import BRAND_CONTEXT, CONTENT_CALENDAR
from src.tools.content_generator import (
    generate_linkedin_post,
    generate_twitter_post,
    generate_campaign_content_plan,
    fetch_post_image,
)
from src.tools.publishers import publish_post
from src.lib.database import (
    save_post,
    get_recent_posts,
    create_campaign,
    get_analytics_summary,
)

load_dotenv()
set_tracing_disabled(True)


def _get_model() -> OpenAIChatCompletionsModel:
    """OpenRouter-backed model for the Agents SDK."""
    client = AsyncOpenAI(
        api_key=os.environ.get("OPENROUTER_API_KEY", ""),
        base_url=os.environ.get("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"),
        default_headers={
            "HTTP-Referer": "https://primemash.com",
            "X-Title": "Primemash Marketing Agent",
        },
    )
    return OpenAIChatCompletionsModel(
        model=os.environ.get("OPENROUTER_MODEL", "anthropic/claude-3.5-sonnet"),
        openai_client=client,
    )


# ── Tools ─────────────────────────────────────────────────────────────────────

@function_tool
def get_todays_theme() -> str:
    """Get today's recommended content theme."""
    day   = datetime.now().strftime("%A").lower()
    theme = CONTENT_CALENDAR.get(day, "educational")
    return json.dumps({"day": day, "theme": theme})


@function_tool
def write_linkedin_post(content_type: str, topic: str) -> str:
    """
    Write a LinkedIn post and fetch a matching image.
    content_type: educational | case_study | thought_leadership | social_proof | product_showcase | motivation_and_tips
    topic: specific subject for this post
    Returns content text and image_url.
    """
    content   = generate_linkedin_post(content_type, topic)
    image_url = fetch_post_image(content, "linkedin")
    return json.dumps({
        "content":      content,
        "image_url":    image_url,
        "platform":     "linkedin",
        "content_type": content_type,
    })


@function_tool
def write_twitter_post(content_type: str, topic: str) -> str:
    """
    Write a tweet (max 280 chars) and fetch a matching image.
    content_type: tip | stat | question | hot_take | thread_opener
    topic: specific subject for this post
    Returns content text and image_url.
    """
    content   = generate_twitter_post(content_type, topic)
    image_url = fetch_post_image(content, "twitter")
    return json.dumps({
        "content":      content,
        "image_url":    image_url,
        "platform":     "twitter",
        "content_type": content_type,
    })


@function_tool
def save_and_publish_linkedin(content: str, content_type: str) -> str:
    """
    Save a LinkedIn post to the database AND publish it live.
    Returns success/failure with post ID.
    """
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"save_and_publish_linkedin called, content length={len(content)}")

    # Publish first — DB save is secondary
    result = publish_post("linkedin", content)
    logger.info(f"LinkedIn publish result: {result}")

    # Save to DB — failure here must NOT trigger a retry
    post_id = None
    try:
        post = save_post(
            platform="linkedin",
            content=content,
            content_type=content_type,
            status="published" if result.get("success") else "failed",
        )
        post_id = post["id"]
    except Exception as e:
        logger.warning(f"DB save failed (non-fatal): {e}")

    if result.get("success"):
        return json.dumps({
            "success": True,
            "platform": "linkedin",
            "db_id": post_id,
            "linkedin_post_id": result.get("post_id"),
            "note": "published successfully" + ("" if post_id else " (db save failed but post is live)"),
        })

    return json.dumps({
        "success": False,
        "platform": "linkedin",
        "error": result.get("error"),
        "note": "do not retry — report this error to the user",
    })


@function_tool
def save_and_publish_twitter(content: str, content_type: str) -> str:
    """
    Save a tweet to the database AND publish it live.
    Returns success/failure with post ID.
    """
    # Truncate to 280 chars
    if len(content) > 280:
        content = content[:277] + "..."

    import logging
    logger = logging.getLogger(__name__)

    # Publish first — DB save is secondary
    result = publish_post("twitter", content)
    logger.info(f"Twitter publish result: {result}")

    # Save to DB — failure here must NOT trigger a retry
    post_id = None
    try:
        post = save_post(
            platform="twitter",
            content=content,
            content_type=content_type,
            status="published" if result.get("success") else "failed",
        )
        post_id = post["id"]
    except Exception as e:
        logger.warning(f"DB save failed (non-fatal): {e}")

    if result.get("success"):
        return json.dumps({
            "success": True,
            "platform": "twitter",
            "db_id": post_id,
            "tweet_id": result.get("post_id"),
            "note": "published successfully" + ("" if post_id else " (db save failed but tweet is live)"),
        })

    return json.dumps({
        "success": False,
        "platform": "twitter",
        "error": result.get("error"),
        "note": "do not retry — report this error to the user",
    })


@function_tool
def save_draft(platform: str, content: str, content_type: str) -> str:
    """Save a post as a draft without publishing."""
    try:
        post = save_post(
            platform=platform,
            content=content,
            content_type=content_type,
            status="draft",
        )
        return json.dumps({"success": True, "post_id": post["id"]})
    except Exception as e:
        return json.dumps({"success": False, "error": str(e)})


@function_tool
def get_recent_posts_tool(limit: int = 10) -> str:
    """Get recent posts from the database."""
    try:
        posts = get_recent_posts(limit)
        return json.dumps(posts, default=str)
    except Exception as e:
        return json.dumps({"error": str(e)})


@function_tool
def get_analytics() -> str:
    """Get analytics summary across all platforms."""
    try:
        return json.dumps(get_analytics_summary())
    except Exception as e:
        return json.dumps({"error": str(e)})


@function_tool
def create_campaign_tool(
    name: str,
    objective: str,
    platforms: str,
    duration_days: int,
) -> str:
    """
    Create a campaign and generate its content calendar.
    platforms: comma-separated e.g. 'linkedin,twitter'
    """
    try:
        platform_list = [p.strip() for p in platforms.split(",")]
        campaign = create_campaign(name, objective, platform_list, duration_days)
        plan = generate_campaign_content_plan(name, objective, platform_list, duration_days)
        return json.dumps({
            "success": True,
            "campaign_id": campaign["id"],
            "plan": plan,
        })
    except Exception as e:
        return json.dumps({"success": False, "error": str(e)})


# ── Agent ─────────────────────────────────────────────────────────────────────

AGENT_INSTRUCTIONS = f"""You are the autonomous marketing agent for Primemash Technologies.

{BRAND_CONTEXT}

You have these tools — use them directly, in sequence, without asking questions:

CONTENT TOOLS:
- get_todays_theme         → get today's recommended content theme
- write_linkedin_post      → generate LinkedIn post text
- write_twitter_post       → generate tweet text (max 280 chars)

PUBLISHING TOOLS (these save AND publish in one step):
- save_and_publish_linkedin  → publish to LinkedIn live + save to DB
- save_and_publish_twitter   → publish to Twitter live + save to DB
- save_draft                 → save without publishing

DATA TOOLS:
- get_recent_posts_tool    → list recent posts
- get_analytics            → performance summary
- create_campaign_tool     → create campaign + content calendar

STRICT RULES:
1. NEVER ask questions. Choose sensible defaults and execute.
2. NEVER just return content and stop — always call save_and_publish_* to actually post it.
3. Call save_and_publish_linkedin and save_and_publish_twitter EXACTLY ONCE each. NEVER retry publishing even if you see a db error — the post is already live.
4. A db_save error in the result is NOT a failure — the post is live. Report success.
3. For "post today's content": call get_todays_theme → write_linkedin_post → save_and_publish_linkedin → write_twitter_post → save_and_publish_twitter → report results.
4. For "generate a post": write it → save_and_publish it → done.
5. For "show analytics": call get_analytics → summarise → done.
6. For "create a campaign": call create_campaign_tool → return plan → done.
7. Report results only after all tools have been called. One final summary, nothing else.

Active platforms: LinkedIn and Twitter. Instagram is disabled.
"""


def build_agent() -> Agent:
    """Build the single marketing agent with all tools attached."""
    return Agent(
        name="PrimemashMarketingAgent",
        model=_get_model(),
        instructions=AGENT_INSTRUCTIONS,
        tools=[
            get_todays_theme,
            write_linkedin_post,
            write_twitter_post,
            save_and_publish_linkedin,
            save_and_publish_twitter,
            save_draft,
            get_recent_posts_tool,
            get_analytics,
            create_campaign_tool,
        ],
    )


# Keep build_team as alias so api.py and scheduler.py don't need changes
def build_team() -> Agent:
    return build_agent()


def _run_agent_sync(task: str, context: dict = None) -> str:
    """Run the agent synchronously in a dedicated event loop (thread-safe)."""
    import asyncio

    agent = build_agent()
    input_message = task
    if context:
        input_message = f"{task}\n\nContext: {json.dumps(context)}"

    # Create a fresh event loop for this thread — avoids FastAPI loop conflicts
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        result = loop.run_until_complete(
            Runner.run(agent, input_message, max_turns=20)
        )
        return result.final_output
    finally:
        loop.close()


async def run_agent_task(task: str, context: dict = None) -> str:
    """Run the agent in a thread executor so it does not block FastAPI's event loop."""
    import asyncio
    from concurrent.futures import ThreadPoolExecutor

    loop = asyncio.get_event_loop()
    with ThreadPoolExecutor(max_workers=1) as executor:
        result = await loop.run_in_executor(
            executor,
            _run_agent_sync,
            task,
            context,
        )
    return result
