"""
Quick helper — fetch your LinkedIn Person URN using an existing access token.
Run this if the main token script couldn't fetch the URN automatically.

Usage:
    uv run python scripts/get_linkedin_urn.py
"""

import os
import json
import urllib.request
from dotenv import load_dotenv

load_dotenv()

token = os.environ.get("LINKEDIN_ACCESS_TOKEN", "").strip()
if not token:
    print("❌  LINKEDIN_ACCESS_TOKEN not set in your .env file.")
    print("    Run scripts/get_linkedin_token.py first to get a token.")
    raise SystemExit(1)

print("🔍 Trying /v2/me ...")
endpoints = [
    ("https://api.linkedin.com/v2/me", "id"),
    ("https://api.linkedin.com/v2/userinfo", "sub"),
]

for url, id_field in endpoints:
    try:
        req = urllib.request.Request(
            url,
            headers={
                "Authorization": f"Bearer {token}",
                "X-Restli-Protocol-Version": "2.0.0",
                "LinkedIn-Version": "202304",
            },
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read())
            person_id = data.get(id_field, "")
            if person_id:
                urn = f"urn:li:person:{person_id}"
                print(f"\n✅ Success via {url}")
                print(f"\n📋 Add this to your .env file:\n")
                print(f"LINKEDIN_PERSON_URN={urn}\n")
                raise SystemExit(0)
    except urllib.error.HTTPError as e:
        print(f"   ⚠️  {url} → HTTP {e.code}. Trying next endpoint...")
    except Exception as e:
        print(f"   ⚠️  {url} → {e}. Trying next endpoint...")

# Both failed — token works but profile access not yet granted
print("\n❌ Both endpoints returned 403.")
print("\nFix: Go to linkedin.com/developers → your app → Products tab")
print("     → Request access to 'Sign In with LinkedIn using OpenID Connect'")
print("     → It approves instantly. Wait 2 minutes then re-run this script.\n")
