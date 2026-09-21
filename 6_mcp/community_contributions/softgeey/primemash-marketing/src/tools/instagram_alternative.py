"""
Instagram Publisher — Alternative Implementation
================================================
Since Meta has restricted developer account creation, this module
provides TWO fallback strategies for Instagram publishing:

Strategy A (Recommended): Buffer API
  - Buffer is a Meta Marketing Partner with approved Instagram access
  - Sign up free at buffer.com, connect your Instagram Business account
  - No Meta developer approval needed

Strategy B: Make.com webhook
  - Create a Make.com scenario that receives a webhook and posts to Instagram
  - Completely bypasses Meta Graph API restrictions

Set INSTAGRAM_STRATEGY=buffer or INSTAGRAM_STRATEGY=make in your .env
"""

import os
import json
import httpx
from typing import Optional
from tenacity import retry, stop_after_attempt, wait_exponential
from dotenv import load_dotenv

load_dotenv()

STRATEGY = os.environ.get("INSTAGRAM_STRATEGY", "buffer")


# ── Strategy A: Buffer API ────────────────────────────────────────────────────

@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2, max=10))
def publish_via_buffer(caption: str, image_url: Optional[str] = None) -> dict:
    """
    Post to Instagram via Buffer's API.

    Setup:
    1. Sign up at buffer.com (free plan works)
    2. Connect your Instagram Business account in Buffer
    3. Go to buffer.com/developers → create an Access Token
    4. Set BUFFER_ACCESS_TOKEN and BUFFER_INSTAGRAM_PROFILE_ID in .env

    Find your profile ID:
        GET https://api.bufferapp.com/1/profiles.json?access_token=YOUR_TOKEN
        Look for the profile where 'service' == 'instagram'
    """
    token      = os.environ.get("BUFFER_ACCESS_TOKEN")
    profile_id = os.environ.get("BUFFER_INSTAGRAM_PROFILE_ID")

    if not token or not profile_id:
        return {
            "success": False,
            "error": "BUFFER_ACCESS_TOKEN and BUFFER_INSTAGRAM_PROFILE_ID not set. "
                     "Sign up at buffer.com and connect your Instagram account.",
        }

    payload: dict = {
        "profile_ids[]": profile_id,
        "text": caption,
        "now": "true",   # post immediately (set to false to queue)
    }
    if image_url:
        payload["media[photo]"] = image_url

    with httpx.Client(timeout=30) as client:
        resp = client.post(
            "https://api.bufferapp.com/1/updates/create.json",
            params={"access_token": token},
            data=payload,
        )

    if resp.status_code == 200:
        data = resp.json()
        post_id = data.get("updates", [{}])[0].get("id", "unknown")
        return {"success": True, "platform": "instagram", "post_id": post_id, "strategy": "buffer"}

    return {
        "success": False,
        "platform": "instagram",
        "error": f"Buffer API {resp.status_code}: {resp.text}",
        "strategy": "buffer",
    }


# ── Strategy B: Make.com webhook ─────────────────────────────────────────────

@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2, max=10))
def publish_via_make_webhook(caption: str, image_url: Optional[str] = None) -> dict:
    """
    Post to Instagram via a Make.com webhook scenario.

    Setup:
    1. Sign up at make.com (free plan: 1,000 ops/month)
    2. Create new Scenario:
       - Trigger: Webhooks → Custom webhook (copy the URL)
       - Action:  Instagram for Business → Create a Photo Post
    3. Set MAKE_INSTAGRAM_WEBHOOK_URL in .env

    The webhook receives: { "caption": "...", "image_url": "..." }
    """
    webhook_url = os.environ.get("MAKE_INSTAGRAM_WEBHOOK_URL")

    if not webhook_url:
        return {
            "success": False,
            "error": "MAKE_INSTAGRAM_WEBHOOK_URL not set. "
                     "Create a Make.com scenario with an Instagram module.",
        }

    payload = {"caption": caption, "image_url": image_url or ""}

    with httpx.Client(timeout=30) as client:
        resp = client.post(webhook_url, json=payload)

    if resp.status_code in (200, 204):
        return {"success": True, "platform": "instagram", "strategy": "make_webhook"}

    return {
        "success": False,
        "platform": "instagram",
        "error": f"Make webhook {resp.status_code}: {resp.text}",
        "strategy": "make_webhook",
    }


# ── Unified entry point ───────────────────────────────────────────────────────

def publish_to_instagram_alternative(caption: str, image_url: Optional[str] = None) -> dict:
    """Route Instagram publishing to the configured strategy."""
    if STRATEGY == "make":
        return publish_via_make_webhook(caption, image_url)
    return publish_via_buffer(caption, image_url)
