import json

from mcp.server.fastmcp import FastMCP

from services.content import get_content_service


mcp = FastMCP("content_server")
service = get_content_service()


@mcp.tool()
def save_idea(topic: str, goal: str, notes: str = "", urls: list[str] | None = None) -> dict:
    return service.save_idea(topic=topic, goal=goal, notes=notes, urls=urls or [])


@mcp.tool()
def create_draft_set(idea_id: str, bundle_id: str, drafts_json: str) -> dict:
    return service.create_draft_set(idea_id=idea_id, bundle_id=bundle_id, drafts_json=drafts_json)


@mcp.tool()
def revise_draft(draft_id: str, revised_draft_json: str, feedback: str = "") -> dict:
    return service.revise_draft(draft_id=draft_id, revised_draft_json=revised_draft_json, feedback=feedback)


@mcp.tool()
def approve_draft(draft_id: str) -> dict:
    return service.approve_draft(draft_id=draft_id)


@mcp.tool()
def reject_draft(draft_id: str, feedback: str = "") -> dict:
    return service.reject_draft(draft_id=draft_id, feedback=feedback)


@mcp.tool()
def record_feedback(draft_id: str, feedback: str) -> dict:
    return service.record_feedback(draft_id=draft_id, feedback=feedback)


@mcp.tool()
def list_drafts(idea_id: str | None = None, limit: int = 50) -> list[dict]:
    return service.list_drafts(idea_id=idea_id, limit=limit)


@mcp.tool()
def store_style_example(content: str, source_label: str) -> dict:
    return service.store_style_example(content=content, source_label=source_label)


@mcp.tool()
def list_post_history(limit: int = 20) -> list[dict]:
    return service.list_post_history(limit=limit)


@mcp.resource("voice://profile")
def voice_profile() -> str:
    return json.dumps(service.voice_resource())


@mcp.resource("history://recent_posts")
def recent_posts() -> str:
    return json.dumps(service.history_resource())


@mcp.resource("draft://{draft_id}")
def draft_resource(draft_id: str) -> str:
    return json.dumps(service.draft_resource(draft_id))


@mcp.resource("sources://{bundle_id}")
def sources_resource(bundle_id: str) -> str:
    return json.dumps(service.sources_resource(bundle_id))


if __name__ == "__main__":
    mcp.run(transport="stdio")
