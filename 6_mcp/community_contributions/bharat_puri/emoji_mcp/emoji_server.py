from mcp.server.fastmcp import FastMCP
from datetime import datetime

mcp = FastMCP("emoji_server")

# Static emoji dictionary
EMOJIS = {
    "smile": "😄",
    "laugh": "😂",
    "wink": "😉",
    "heart": "❤️",
    "thumbs_up": "👍",
    "fire": "🔥",
    "star": "⭐",
    "ok": "👌",

    # Categories
    "animals": {
        "dog": "🐶",
        "cat": "🐱",
        "lion": "🦁",
        "panda": "🐼"
    },

    "food": {
        "pizza": "🍕",
        "burger": "🍔",
        "fries": "🍟",
        "apple": "🍎"
    }
}


# -------------------------------------------------------------------------
# Tool 1: Get a single emoji
# -------------------------------------------------------------------------
@mcp.tool()
async def get_emoji(name: str) -> str:
    """Return an emoji by simple name."""
    if name in EMOJIS:
        return EMOJIS[name]
    # Search subcategories
    for cat in EMOJIS.values():
        if isinstance(cat, dict) and name in cat:
            return cat[name]
    return f"Emoji '{name}' not found."


# -------------------------------------------------------------------------
# Tool 2: List available categories
# -------------------------------------------------------------------------
@mcp.tool()
async def emoji_categories() -> list[str]:
    """Return available emoji categories."""
    return [k for k, v in EMOJIS.items() if isinstance(v, dict)]


# -------------------------------------------------------------------------
# Tool 3: List emojis inside a category
# -------------------------------------------------------------------------
@mcp.tool()
async def list_emojis(category: str) -> dict:
    """Return all emojis for a given category."""
    if category in EMOJIS and isinstance(EMOJIS[category], dict):
        return EMOJIS[category]
    return {"error": f"Category '{category}' not found."}


# -------------------------------------------------------------------------
# Start server
# -------------------------------------------------------------------------
if __name__ == "__main__":
    mcp.run(transport="stdio")

