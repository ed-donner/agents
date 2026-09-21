"""
Social media publisher tools.
LinkedIn  → Make.com webhook (LinkedIn API access pending approval)
Twitter   → Disabled (requires Basic plan $100/month)
Instagram → Disabled (requires Make.com or Buffer setup)

To re-enable Twitter: upgrade to Twitter API Basic, set TWITTER_STRATEGY=enabled
To re-enable Instagram: set INSTAGRAM_STRATEGY=make or buffer
"""

import os
import logging
import json
import httpx
import tweepy
from typing import Optional
from dotenv import load_dotenv
from tenacity import retry, stop_after_attempt, wait_exponential

load_dotenv()

logger = logging.getLogger(__name__)


# ── LinkedIn ──────────────────────────────────────────────────────────────────

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def publish_to_linkedin(content: str, image_url: Optional[str] = None) -> dict:
    """
    Publish to LinkedIn via Make.com webhook.
    Set MAKE_LINKEDIN_WEBHOOK_URL in .env.
    """
    strategy = os.environ.get("LINKEDIN_STRATEGY", "make").lower()
    logger.info(f"LinkedIn publisher called — strategy={strategy}")

    if strategy == "disabled":
        return {
            "success": False,
            "platform": "linkedin",
            "skipped": True,
            "error": "LinkedIn is disabled. Set LINKEDIN_STRATEGY=make in .env.",
        }

    if strategy == "make":
        webhook_url = os.environ.get("MAKE_LINKEDIN_WEBHOOK_URL", "")
        if not webhook_url:
            return {
                "success": False,
                "platform": "linkedin",
                "error": "MAKE_LINKEDIN_WEBHOOK_URL not set in .env",
            }
        logger.info(f"LinkedIn Make webhook: calling {webhook_url[:50]}...")
        payload = {"body": content}
        if image_url:
            payload["image_url"] = image_url
        with httpx.Client(timeout=30) as client:
            r = client.post(webhook_url, json=payload)
        logger.info(f"LinkedIn Make webhook response: HTTP {r.status_code} — {r.text[:100]}")
        if r.status_code in (200, 204):
            logger.info("LinkedIn Make webhook: SUCCESS")
            return {"success": True, "platform": "linkedin", "post_id": "make_webhook"}
        logger.error(f"LinkedIn Make webhook: FAILED HTTP {r.status_code}: {r.text}")
        return {
            "success": False,
            "platform": "linkedin",
            "error": f"Make webhook {r.status_code}: {r.text}",
        }

    # Direct API (keep for when Community Management API is approved)
    access_token = os.environ.get("LINKEDIN_ACCESS_TOKEN")
    person_urn   = os.environ.get("LINKEDIN_PERSON_URN")

    if not access_token or not person_urn:
        return {"success": False, "error": "LinkedIn credentials not configured."}

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
        "X-Restli-Protocol-Version": "2.0.0",
    }
    payload = {
        "author": person_urn,
        "lifecycleState": "PUBLISHED",
        "specificContent": {
            "com.linkedin.ugc.ShareContent": {
                "shareCommentary": {"text": content},
                "shareMediaCategory": "NONE",
            }
        },
        "visibility": {"com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"},
    }
    with httpx.Client(timeout=30) as client:
        r = client.post(
            "https://api.linkedin.com/v2/ugcPosts",
            headers=headers,
            json=payload,
        )
    if r.status_code in (200, 201):
        return {"success": True, "platform": "linkedin",
                "post_id": r.headers.get("x-restli-id", "unknown")}
    return {
        "success": False,
        "platform": "linkedin",
        "error": f"HTTP {r.status_code}: {r.text}",
    }


# ── X (Twitter) ───────────────────────────────────────────────────────────────

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def publish_to_twitter(content: str, image_url: Optional[str] = None) -> dict:
    """
    Publish a tweet via Tweepy (OAuth 1.0a).
    Requires Twitter API Basic plan ($100/month) for write access.
    Set TWITTER_STRATEGY=enabled once upgraded.
    """
    strategy = os.environ.get("TWITTER_STRATEGY", "disabled").lower()

    if strategy == "disabled":
        return {
            "success": False,
            "platform": "twitter",
            "skipped": True,
            "error": "Twitter is disabled. Upgrade to Twitter API Basic plan then set TWITTER_STRATEGY=enabled.",
        }

    api_key             = os.environ.get("TWITTER_API_KEY")
    api_secret          = os.environ.get("TWITTER_API_SECRET")
    access_token        = os.environ.get("TWITTER_ACCESS_TOKEN")
    access_token_secret = os.environ.get("TWITTER_ACCESS_TOKEN_SECRET")

    if not all([api_key, api_secret, access_token, access_token_secret]):
        return {"success": False, "error": "Twitter credentials not configured."}

    if len(content) > 280:
        content = content[:277] + "..."

    client = tweepy.Client(
        consumer_key=api_key,
        consumer_secret=api_secret,
        access_token=access_token,
        access_token_secret=access_token_secret,
    )
    try:
        r = client.create_tweet(text=content)
        return {"success": True, "platform": "twitter", "post_id": str(r.data["id"])}
    except tweepy.TweepyException as e:
        return {"success": False, "platform": "twitter", "error": str(e)}


# ── Instagram ─────────────────────────────────────────────────────────────────

def publish_to_instagram(content: str, image_url: Optional[str] = None) -> dict:
    """
    Instagram publishing via Make.com webhook or Buffer.
    Set INSTAGRAM_STRATEGY=make or buffer in .env to enable.
    """
    strategy = os.environ.get("INSTAGRAM_STRATEGY", "disabled").lower()

    if strategy == "disabled":
        return {
            "success": False,
            "platform": "instagram",
            "skipped": True,
            "error": "Instagram is disabled. Set INSTAGRAM_STRATEGY=make or buffer in .env.",
        }

    from src.tools.instagram_alternative import publish_to_instagram_alternative
    return publish_to_instagram_alternative(content, image_url)


# ── Unified publisher ─────────────────────────────────────────────────────────

def publish_post(platform: str, content: str, image_url: Optional[str] = None) -> dict:
    """Route a post to the correct platform publisher."""
    publishers = {
        "linkedin":  publish_to_linkedin,
        "twitter":   publish_to_twitter,
        "instagram": publish_to_instagram,
    }
    publisher = publishers.get(platform.lower())
    if not publisher:
        return {"success": False, "error": f"Unknown platform: {platform}"}
    return publisher(content, image_url)
