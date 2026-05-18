from __future__ import annotations

from typing import Iterable


def parse_urls(raw: str) -> list[str]:
    items = []
    for chunk in raw.replace(",", "\n").splitlines():
        value = chunk.strip()
        if value:
            items.append(value)
    return items


def compose_post_body(body: str, cta: str = "") -> str:
    value = body.strip()
    cta = cta.strip()
    if cta and cta not in value:
        value = f"{value}\n\n{cta}"
    return value


def draft_choices(drafts: Iterable[dict]) -> list[tuple[str, str]]:
    choices = []
    for draft in drafts:
        label = f"{draft['variant']} | {draft['status']} | {draft['id'][:8]}"
        choices.append((label, draft["id"]))
    return choices


def format_auth_status(status: dict) -> str:
    if not status.get("valid"):
        return f"LinkedIn session: not connected\nReason: {status.get('reason', 'unknown')}"
    session = status["session"]
    return (
        "LinkedIn session: connected\n"
        f"Name: {session.get('name', '')}\n"
        f"Person URN: {session.get('person_urn', '')}\n"
        f"Expires At: {session.get('expires_at', '')}"
    )


def format_draft(draft: dict) -> str:
    link_line = f"\nLink: {draft['link_url']}" if draft.get("link_url") else ""
    cta_line = f"\nCTA: {draft['cta']}" if draft.get("cta") else ""
    return (
        f"Variant: {draft['variant']}\n"
        f"Status: {draft['status']}\n"
        f"Score: {draft['score']}\n"
        f"Confidence: {draft['confidence']}\n"
        f"Similarity: {draft['similarity_score']}\n"
        f"Title: {draft['title']}\n"
        f"Rationale: {draft['rationale']}\n\n"
        f"{draft['body']}"
        f"{cta_line}"
        f"{link_line}"
    )


def format_bundle(bundle: dict) -> str:
    lines = [
        f"Bundle: {bundle['id']}",
        f"Summary: {bundle['summary']}",
        "",
        "Sources:",
    ]
    for source in bundle.get("sources", []):
        lines.append(f"- {source['title']} | {source['url']}")
        if source.get("snippet"):
            lines.append(f"  {source['snippet']}")
    return "\n".join(lines)


def format_history(posts: list[dict]) -> str:
    if not posts:
        return "No published posts yet."
    lines = []
    for post in posts:
        commentary = (
            post.get("payload", {})
            .get("specificContent", {})
            .get("com.linkedin.ugc.ShareContent", {})
            .get("shareCommentary", {})
            .get("text", "")
        )
        lines.append(
            f"{post['created_at']} | {post['post_urn']}\n"
            f"Draft: {post['draft_id']}\n"
            f"{commentary}\n"
        )
    return "\n\n".join(lines)


def format_voice_profile(profile: dict) -> str:
    lines = [f"Average Length: {profile.get('average_length', 0)}", ""]
    lines.append("Examples:")
    for example in profile.get("voice_examples", []):
        lines.append(f"- {example['source_label']}: {example['content'][:220]}")
    return "\n".join(lines)
