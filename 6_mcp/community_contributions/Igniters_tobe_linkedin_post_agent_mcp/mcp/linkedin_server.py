import json

from mcp.server.fastmcp import FastMCP

from services.linkedin import get_linkedin_service


mcp = FastMCP("linkedin_server")
service = get_linkedin_service()


@mcp.tool()
def get_auth_url() -> dict:
    return service.get_auth_url()


@mcp.tool()
def exchange_code(code: str) -> dict:
    return service.exchange_code(code=code)


@mcp.tool()
def whoami() -> dict:
    return service.whoami()


@mcp.tool()
def validate_session() -> dict:
    return service.validate_session()


@mcp.tool()
def publish_text_post(draft_id: str, content: str, visibility: str = "PUBLIC") -> dict:
    return service.publish_text_post(draft_id=draft_id, content=content, visibility=visibility)


@mcp.tool()
def publish_link_post(
    draft_id: str,
    content: str,
    original_url: str,
    title: str = "",
    description: str = "",
    visibility: str = "PUBLIC",
) -> dict:
    return service.publish_link_post(
        draft_id=draft_id,
        content=content,
        original_url=original_url,
        title=title,
        description=description,
        visibility=visibility,
    )


@mcp.tool()
def list_recent_posts(limit: int = 20) -> list[dict]:
    return service.list_recent_posts(limit=limit)


if __name__ == "__main__":
    mcp.run(transport="stdio")
