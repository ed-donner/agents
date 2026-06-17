"""
Tests LinkedIn and Twitter publishing directly with your credentials.
Run this to see the exact API error before the agent touches anything.

Usage:
    uv run python scripts/test_publishing.py
"""

import os, json
from dotenv import load_dotenv
load_dotenv()

print("=" * 55)
print("Primemash — Publishing Credentials Test")
print("=" * 55)

# ── Check env vars are present ────────────────────────────────
print("\n1. Checking .env values...\n")

linkedin_token = os.environ.get("LINKEDIN_ACCESS_TOKEN", "")
linkedin_urn   = os.environ.get("LINKEDIN_PERSON_URN", "")
tw_api_key     = os.environ.get("TWITTER_API_KEY", "")
tw_api_secret  = os.environ.get("TWITTER_API_SECRET", "")
tw_token       = os.environ.get("TWITTER_ACCESS_TOKEN", "")
tw_token_sec   = os.environ.get("TWITTER_ACCESS_TOKEN_SECRET", "")

def check(label, value):
    if value:
        print(f"   ✅ {label}: {value[:12]}...{value[-4:]}")
    else:
        print(f"   ❌ {label}: NOT SET")

check("LINKEDIN_ACCESS_TOKEN",        linkedin_token)
check("LINKEDIN_PERSON_URN",          linkedin_urn)
check("TWITTER_API_KEY",              tw_api_key)
check("TWITTER_API_SECRET",           tw_api_secret)
check("TWITTER_ACCESS_TOKEN",         tw_token)
check("TWITTER_ACCESS_TOKEN_SECRET",  tw_token_sec)

# ── Test LinkedIn ─────────────────────────────────────────────
print("\n2. Testing LinkedIn API...\n")
import httpx

if linkedin_token and linkedin_urn:
    payload = {
        "author": linkedin_urn,
        "lifecycleState": "PUBLISHED",
        "specificContent": {
            "com.linkedin.ugc.ShareContent": {
                "shareCommentary": {"text": "Primemash test post — please ignore."},
                "shareMediaCategory": "NONE",
            }
        },
        "visibility": {"com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"},
    }
    try:
        r = httpx.post(
            "https://api.linkedin.com/v2/ugcPosts",
            headers={
                "Authorization": f"Bearer {linkedin_token}",
                "Content-Type": "application/json",
                "X-Restli-Protocol-Version": "2.0.0",
            },
            json=payload,
            timeout=15,
        )
        if r.status_code in (200, 201):
            post_id = r.headers.get("x-restli-id", "unknown")
            print(f"   ✅ LinkedIn: SUCCESS — post ID: {post_id}")
        else:
            print(f"   ❌ LinkedIn: HTTP {r.status_code}")
            print(f"   Response: {r.text}")
    except Exception as e:
        print(f"   ❌ LinkedIn: Exception — {e}")
else:
    print("   ⏭  LinkedIn: skipped (credentials missing)")

# ── Test Twitter ──────────────────────────────────────────────
print("\n3. Testing Twitter API...\n")

if all([tw_api_key, tw_api_secret, tw_token, tw_token_sec]):
    import tweepy
    try:
        client = tweepy.Client(
            consumer_key=tw_api_key,
            consumer_secret=tw_api_secret,
            access_token=tw_token,
            access_token_secret=tw_token_sec,
        )
        r = client.create_tweet(text="Primemash test tweet — please ignore.")
        print(f"   ✅ Twitter: SUCCESS — tweet ID: {r.data['id']}")
    except tweepy.TweepyException as e:
        print(f"   ❌ Twitter: {e}")
    except Exception as e:
        print(f"   ❌ Twitter: Exception — {e}")
else:
    print("   ⏭  Twitter: skipped (credentials missing)")

print("\n" + "=" * 55)
