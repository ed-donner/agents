"""
LinkedIn OAuth 2.0 Token Generator
Generates a fresh access token AND confirms your correct Person URN.

Usage:
    uv run python scripts/get_linkedin_token.py
"""

import os
import sys
import json
import secrets
import webbrowser
import urllib.parse
import urllib.request
from http.server import HTTPServer, BaseHTTPRequestHandler
from dotenv import load_dotenv

load_dotenv()

CLIENT_ID    = os.environ.get("LINKEDIN_CLIENT_ID", "").strip()
CLIENT_SECRET= os.environ.get("LINKEDIN_CLIENT_SECRET", "").strip()
REDIRECT_URI = "http://localhost:8080/callback"
SCOPES       = "w_member_social openid profile email"

_result = {}
_state  = ""


class CallbackHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        params = dict(urllib.parse.parse_qsl(parsed.query))

        if parsed.path != "/callback":
            self._respond(404, "Not found"); return

        if params.get("state") != _state:
            self._respond(400, "State mismatch — try again."); return

        if "error" in params:
            _result["error"] = params.get("error_description", params["error"])
            self._respond(400, f"OAuth error: {_result['error']}"); return

        code = params.get("code")
        if not code:
            self._respond(400, "No code returned."); return

        token_data = self._exchange(code)
        if "error" in token_data:
            _result["error"] = str(token_data)
            self._respond(400, f"Token error: {token_data}"); return

        _result["token_data"] = token_data
        self._respond(200, "Success! Return to your terminal.")

    def _exchange(self, code):
        payload = urllib.parse.urlencode({
            "grant_type":    "authorization_code",
            "code":          code,
            "redirect_uri":  REDIRECT_URI,
            "client_id":     CLIENT_ID,
            "client_secret": CLIENT_SECRET,
        }).encode()
        req = urllib.request.Request(
            "https://www.linkedin.com/oauth/v2/accessToken",
            data=payload,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        with urllib.request.urlopen(req, timeout=15) as r:
            return json.loads(r.read())

    def _respond(self, status, msg):
        body = msg.encode()
        self.send_response(status)
        self.send_header("Content-Type", "text/plain")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *a): pass


def fetch_member_id(token):
    """Try every available endpoint to get the member ID."""
    endpoints = [
        ("https://api.linkedin.com/v2/me", "id"),
        ("https://api.linkedin.com/v2/userinfo", "sub"),
    ]
    for url, field in endpoints:
        try:
            req = urllib.request.Request(
                url,
                headers={
                    "Authorization": f"Bearer {token}",
                    "X-Restli-Protocol-Version": "2.0.0",
                    "LinkedIn-Version": "202304",
                },
            )
            with urllib.request.urlopen(req, timeout=15) as r:
                data = json.loads(r.read())
                member_id = data.get(field, "")
                if member_id:
                    return member_id, url
        except Exception:
            continue
    return None, None


def main():
    global _state

    if not CLIENT_ID or not CLIENT_SECRET:
        print("❌ Set LINKEDIN_CLIENT_ID and LINKEDIN_CLIENT_SECRET in .env first.")
        sys.exit(1)

    _state   = secrets.token_urlsafe(16)
    auth_url = (
        "https://www.linkedin.com/oauth/v2/authorization?"
        + urllib.parse.urlencode({
            "response_type": "code",
            "client_id":     CLIENT_ID,
            "redirect_uri":  REDIRECT_URI,
            "scope":         SCOPES,
            "state":         _state,
        })
    )

    print("\n🔗 LinkedIn Token Generator")
    print("=" * 50)
    print("\nOpening browser — log in and click Allow...")
    webbrowser.open(auth_url)
    print(f"\nIf browser didn't open, visit:\n{auth_url}\n")

    server = HTTPServer(("localhost", 8080), CallbackHandler)
    server.timeout = 120
    server.handle_request()

    if "error" in _result:
        print(f"\n❌ {_result['error']}")
        sys.exit(1)

    token_data   = _result.get("token_data", {})
    access_token = token_data.get("access_token", "")

    if not access_token:
        print("❌ No access token received.")
        sys.exit(1)

    print("✅ Access token obtained!")

    # Fetch member ID
    member_id, source = fetch_member_id(access_token)

    if member_id:
        urn = f"urn:li:member:{member_id}"
        print(f"✅ Member ID confirmed via {source}: {member_id}")
    else:
        print("⚠️  Could not fetch member ID automatically.")
        print("   Check your LinkedIn page source for urn:li:member: as described earlier.")
        urn = "urn:li:member:YOUR_ID_HERE"

    expires  = token_data.get("expires_in", 0)
    days     = int(expires) // 86400 if expires else "unknown"

    print("\n" + "=" * 50)
    print("📋 Add these to your .env file:\n")
    print(f"LINKEDIN_ACCESS_TOKEN={access_token}")
    print(f"LINKEDIN_PERSON_URN={urn}")
    print(f"\n⏱  Token expires in ~{days} days")
    print("\n⚠️  Re-run this script when the token expires.")
    print("=" * 50 + "\n")


if __name__ == "__main__":
    main()
