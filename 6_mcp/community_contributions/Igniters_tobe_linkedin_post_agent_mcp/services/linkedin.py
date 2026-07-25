from __future__ import annotations

import secrets
from datetime import UTC, datetime, timedelta
from functools import lru_cache
from urllib.parse import urlencode

import httpx
import keyring
from keyring.errors import KeyringError

from config.settings import Settings, get_settings
from db.repository import get_repository, now_iso
from models.entities import OAuthSessionMetadata


LINKEDIN_AUTH_URL = "https://www.linkedin.com/oauth/v2/authorization"
LINKEDIN_TOKEN_URL = "https://www.linkedin.com/oauth/v2/accessToken"
LINKEDIN_USERINFO_URL = "https://api.linkedin.com/v2/userinfo"
LINKEDIN_UGC_POSTS_URL = "https://api.linkedin.com/v2/ugcPosts"
LINKEDIN_SCOPES = "openid profile email w_member_social"
LOCAL_POST_CHARACTER_LIMIT = 2800


class LinkedInService:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.repository = get_repository()

    def get_auth_url(self) -> dict:
        self.settings.validate_linkedin()
        state = secrets.token_urlsafe(24)
        query = urlencode(
            {
                "response_type": "code",
                "client_id": self.settings.linkedin_client_id,
                "redirect_uri": self.settings.linkedin_redirect_uri,
                "scope": LINKEDIN_SCOPES,
                "state": state,
            }
        )
        return {"auth_url": f"{LINKEDIN_AUTH_URL}?{query}", "state": state}

    def exchange_code(self, code: str) -> dict:
        self.settings.validate_linkedin()
        payload = {
            "grant_type": "authorization_code",
            "code": code,
            "client_id": self.settings.linkedin_client_id,
            "client_secret": self.settings.linkedin_client_secret,
            "redirect_uri": self.settings.linkedin_redirect_uri,
        }
        with httpx.Client(timeout=20) as client:
            token_response = client.post(LINKEDIN_TOKEN_URL, data=payload)
            token_response.raise_for_status()
        token_data = token_response.json()
        access_token = token_data["access_token"]
        expires_at = datetime.now(UTC) + timedelta(seconds=int(token_data.get("expires_in", 3600)))
        userinfo = self._userinfo(access_token)
        person_urn = f"urn:li:person:{userinfo['sub']}"
        access_token_ref = f"linkedin_access_token:{userinfo['sub']}"
        try:
            keyring.set_password(self.settings.keyring_service_name, access_token_ref, access_token)
        except KeyringError as exc:
            raise RuntimeError("Failed to persist LinkedIn access token to keyring") from exc
        now = now_iso()
        session = OAuthSessionMetadata(
            member_sub=userinfo["sub"],
            person_urn=person_urn,
            name=userinfo.get("name", "LinkedIn Member"),
            email=userinfo.get("email"),
            access_token_ref=access_token_ref,
            expires_at=expires_at.isoformat(),
            created_at=now,
            updated_at=now,
        )
        self.repository.save_oauth_session(session)
        return session.model_dump()

    def whoami(self) -> dict:
        session = self.repository.get_oauth_session()
        if not session:
            raise RuntimeError("No LinkedIn session found")
        return session.model_dump()

    def validate_session(self) -> dict:
        session = self.repository.get_oauth_session()
        if not session:
            return {"valid": False, "reason": "No LinkedIn session found"}
        try:
            access_token = keyring.get_password(self.settings.keyring_service_name, session.access_token_ref)
        except KeyringError as exc:
            return {"valid": False, "reason": f"Keyring error: {exc}"}
        if not access_token:
            return {"valid": False, "reason": "Access token missing from keyring"}
        expires_at = datetime.fromisoformat(session.expires_at)
        if expires_at <= datetime.now(UTC):
            return {"valid": False, "reason": "Access token has expired"}
        return {"valid": True, "session": session.model_dump()}

    def publish_text_post(self, draft_id: str, content: str, visibility: str = "PUBLIC") -> dict:
        payload = self._build_text_payload(content=content, visibility=visibility)
        return self._publish(draft_id=draft_id, payload=payload, link_url=None)

    def publish_link_post(
        self,
        draft_id: str,
        content: str,
        original_url: str,
        title: str = "",
        description: str = "",
        visibility: str = "PUBLIC",
    ) -> dict:
        if not original_url:
            raise RuntimeError("original_url is required for link posts")
        payload = self._build_link_payload(
            content=content,
            original_url=original_url,
            title=title,
            description=description,
            visibility=visibility,
        )
        return self._publish(draft_id=draft_id, payload=payload, link_url=original_url)

    def list_recent_posts(self, limit: int = 20) -> list[dict]:
        return [record.model_dump() for record in self.repository.list_published_posts(limit=limit)]

    def _publish(self, draft_id: str, payload: dict, link_url: str | None) -> dict:
        session_info = self.validate_session()
        if not session_info["valid"]:
            raise RuntimeError(session_info["reason"])
        headers = self._headers()
        with httpx.Client(timeout=20) as client:
            response = client.post(LINKEDIN_UGC_POSTS_URL, json=payload, headers=headers)
        if response.status_code >= 400:
            raise RuntimeError(response.text)
        post_urn = response.headers.get("x-restli-id") or response.headers.get("X-RestLi-Id") or ""
        if not post_urn:
            body = response.json() if response.content else {}
            post_urn = body.get("id", "")
        record = self.repository.save_published_post(
            draft_id=draft_id,
            post_urn=post_urn,
            author_urn=payload["author"],
            payload=payload,
            response=response.json() if response.content else {"status_code": response.status_code},
            link_url=link_url,
        )
        return record.model_dump()

    def _build_text_payload(self, content: str, visibility: str) -> dict:
        self._validate_content(content)
        session = self.repository.get_oauth_session()
        if not session:
            raise RuntimeError("No LinkedIn session found")
        return {
            "author": session.person_urn,
            "lifecycleState": "PUBLISHED",
            "specificContent": {
                "com.linkedin.ugc.ShareContent": {
                    "shareCommentary": {"text": content},
                    "shareMediaCategory": "NONE",
                }
            },
            "visibility": {"com.linkedin.ugc.MemberNetworkVisibility": visibility},
        }

    def _build_link_payload(
        self,
        content: str,
        original_url: str,
        title: str,
        description: str,
        visibility: str,
    ) -> dict:
        self._validate_content(content)
        session = self.repository.get_oauth_session()
        if not session:
            raise RuntimeError("No LinkedIn session found")
        media: dict = {"status": "READY", "originalUrl": original_url}
        if title:
            media["title"] = {"text": title}
        if description:
            media["description"] = {"text": description}
        return {
            "author": session.person_urn,
            "lifecycleState": "PUBLISHED",
            "specificContent": {
                "com.linkedin.ugc.ShareContent": {
                    "shareCommentary": {"text": content},
                    "shareMediaCategory": "ARTICLE",
                    "media": [media],
                }
            },
            "visibility": {"com.linkedin.ugc.MemberNetworkVisibility": visibility},
        }

    def _validate_content(self, content: str) -> None:
        if not content.strip():
            raise RuntimeError("Post content cannot be empty")
        if len(content) > LOCAL_POST_CHARACTER_LIMIT:
            raise RuntimeError(
                f"Post content exceeds the configured safety limit of {LOCAL_POST_CHARACTER_LIMIT} characters"
            )

    def _headers(self) -> dict[str, str]:
        session = self.repository.get_oauth_session()
        if not session:
            raise RuntimeError("No LinkedIn session found")
        try:
            token = keyring.get_password(self.settings.keyring_service_name, session.access_token_ref)
        except KeyringError as exc:
            raise RuntimeError("Failed to read LinkedIn access token from keyring") from exc
        if not token:
            raise RuntimeError("Access token missing from keyring")
        return {
            "Authorization": f"Bearer {token}",
            "X-Restli-Protocol-Version": "2.0.0",
            "Content-Type": "application/json",
        }

    def _userinfo(self, access_token: str) -> dict:
        with httpx.Client(timeout=20) as client:
            response = client.get(
                LINKEDIN_USERINFO_URL,
                headers={"Authorization": f"Bearer {access_token}"},
            )
            response.raise_for_status()
        return response.json()


@lru_cache(maxsize=1)
def get_linkedin_service() -> LinkedInService:
    return LinkedInService(get_settings())
