"""
Curiosity Break MCP — tiny server for fun facts (no API keys).

Modes:
  python server.py                    → stdio (Cursor / Agents SDK)
  python server.py --streamable-http  → HTTP (browser at /, MCP at /mcp)

"""

import html
import os
import sys
from typing import Any

import httpx
from mcp.server.fastmcp import FastMCP
from starlette.requests import Request
from starlette.responses import HTMLResponse


def _listen_host() -> str:
    return os.environ.get("FASTMCP_HOST", "127.0.0.1")


def _listen_port() -> int:
    for key in ("FASTMCP_PORT", "PORT"):
        val = os.environ.get(key)
        if val:
            return int(val)
    return 8000


mcp = FastMCP(
    "curiosity_break",
    host=_listen_host(),
    port=_listen_port(),
)


async def _fetch_xkcd_for_dashboard(
    client: httpx.AsyncClient, raw_num: str
) -> tuple[dict[str, Any] | None, str | None]:
    """Return comic JSON or None with a user-safe error message."""
    try:
        if raw_num.isdigit():
            url = f"https://xkcd.com/{int(raw_num)}/info.0.json"
        else:
            url = "https://xkcd.com/info.0.json"
        r = await client.get(url)
        r.raise_for_status()
        data = r.json()
        if not isinstance(data, dict):
            return None, "XKCD returned an unexpected response."
        for key in ("title", "alt", "num", "img"):
            if key not in data:
                return None, "Could not parse the comic data. Try again later."
        try:
            int(data["num"])
        except (TypeError, ValueError):
            return None, "Could not parse the comic data. Try again later."
        return data, None
    except httpx.HTTPError:
        return None, "Could not load the comic (XKCD may be unreachable). Try another number or reload later."
    except (ValueError, KeyError, TypeError):
        return None, "Could not parse the comic data. Try again later."


async def _fetch_advice_for_dashboard(client: httpx.AsyncClient) -> tuple[str | None, str | None]:
    """Return advice text or None with a user-safe error message."""
    try:
        r = await client.get("https://api.adviceslip.com/advice")
        r.raise_for_status()
        slip = r.json()["slip"]
        advice = slip["advice"]
        if not isinstance(advice, str):
            return None, "Advice Slip returned an unexpected response."
        return advice, None
    except httpx.HTTPError:
        return None, "Could not load random advice (Advice Slip may be unreachable). Reload to try again."
    except (ValueError, KeyError, TypeError):
        return None, "Could not parse advice. Reload to try again."


@mcp.tool()
async def random_advice() -> str:
    """Return a random short piece of life advice (public Advice Slip API)."""
    async with httpx.AsyncClient(timeout=15.0) as client:
        r = await client.get("https://api.adviceslip.com/advice")
        r.raise_for_status()
        slip = r.json()["slip"]
        return f'#{slip["id"]}: {slip["advice"]}'


@mcp.tool()
async def xkcd_latest() -> str:
    """Return title, alt text, and image URL for the latest XKCD comic."""
    async with httpx.AsyncClient(timeout=15.0) as client:
        r = await client.get("https://xkcd.com/info.0.json")
        r.raise_for_status()
        data = r.json()
        return (
            f"#{data['num']} — {data['title']}\n"
            f"Alt: {data['alt']}\n"
            f"Image: {data['img']}"
        )


@mcp.tool()
async def xkcd_by_number(comic_number: int) -> str:
    """Fetch a specific XKCD comic by number (e.g. 303 for \"Compiling\")."""
    async with httpx.AsyncClient(timeout=15.0) as client:
        r = await client.get(f"https://xkcd.com/{comic_number}/info.0.json")
        r.raise_for_status()
        data = r.json()
        return (
            f"#{data['num']} — {data['title']}\n"
            f"Alt: {data['alt']}\n"
            f"Image: {data['img']}"
        )


@mcp.custom_route("/", methods=["GET"])
async def browser_dashboard(request: Request) -> HTMLResponse:
    """Human-readable dashboard; MCP clients use /mcp."""
    raw_num = request.query_params.get("num", "").strip()
    async with httpx.AsyncClient(timeout=15.0) as client:
        comic, comic_err = await _fetch_xkcd_for_dashboard(client, raw_num)
        advice_text, advice_err = await _fetch_advice_for_dashboard(client)

    mcp_path = html.escape(getattr(mcp.settings, "streamable_http_path", "/mcp"))

    if comic is not None:
        title = html.escape(str(comic["title"]))
        alt = html.escape(str(comic["alt"]))
        num = int(comic["num"])
        img_url = str(comic["img"])
        w = comic.get("width", "")
        h = comic.get("height", "")
        comic_body = f"""<p><strong>#{num} — {title}</strong></p>
    <p class="muted">Alt: {alt}</p>
    <img src="{html.escape(img_url, quote=True)}" alt="{alt}" width="{w}" height="{h}" />"""
    else:
        comic_body = f'<p class="muted">{html.escape(comic_err or "Could not load the comic.")}</p>'
        num = 0

    if advice_text is not None:
        advice_block = f"<p>{html.escape(advice_text)}</p>"
    else:
        advice_block = f'<p class="muted">{html.escape(advice_err or "Could not load advice.")}</p>'

    page = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Curiosity Break</title>
  <style>
    :root {{ font-family: system-ui, sans-serif; background: #0f1419; color: #e7e9ea; }}
    body {{ max-width: 52rem; margin: 2rem auto; padding: 0 1rem; line-height: 1.5; }}
    a {{ color: #6db3f2; }}
    img {{ max-width: 100%; height: auto; border-radius: 8px; margin-top: 0.75rem; }}
    .card {{ background: #1a2332; border-radius: 12px; padding: 1.25rem; margin-bottom: 1.5rem; }}
    .muted {{ color: #8b98a5; font-size: 0.9rem; }}
    input, button {{ padding: 0.5rem 0.75rem; border-radius: 8px; border: 1px solid #38444d; background: #22303c; color: inherit; }}
    button {{ cursor: pointer; }}
    h1 {{ font-size: 1.35rem; }}
  </style>
</head>
<body>
  <h1>Curiosity Break</h1>
  <p class="muted">Human page — reload for a new random advice. MCP clients connect to <code>{mcp_path}</code> (JSON-RPC), not here.</p>

  <div class="card">
    <h2>Latest XKCD (or pick a number)</h2>
    {comic_body}
    <form method="get" action="/" style="margin-top:1rem;display:flex;gap:0.5rem;align-items:center;flex-wrap:wrap;">
      <label>Comic # <input name="num" type="number" min="1" placeholder="{num or ''}" style="width:6rem;" /></label>
      <button type="submit">Load</button>
      <a href="/">Reset to latest</a>
    </form>
  </div>

  <div class="card">
    <h2>Random advice</h2>
    {advice_block}
    <p class="muted"><a href="/">Reload page</a> for another slip.</p>
  </div>
</body>
</html>"""
    return HTMLResponse(page)


def main() -> None:
    transport = "stdio"
    if len(sys.argv) > 1:
        arg = sys.argv[1].lower().strip("-")
        if arg in ("streamable-http", "http"):
            transport = "streamable-http"
        elif arg == "sse":
            transport = "sse"
        elif arg in ("help", "h"):
            print(__doc__)
            return
    mcp.run(transport=transport)  # type: ignore[arg-type]


if __name__ == "__main__":
    main()
