"""MCP server: align local .env files with .env.example (read-only, repo-local)."""

from __future__ import annotations

import json
from pathlib import Path

from mcp.server.fastmcp import FastMCP

from env_io import (
    EnvAlignError,
    compare_example_to_env,
    mask_value,
    parse_dotenv_detailed,
    parse_dotenv_text,
    resolve_under_root,
)

mcp = FastMCP("env_align")


def _read_text(path: Path) -> str | None:
    if not path.is_file():
        return None
    return path.read_text(encoding="utf-8", errors="replace")


@mcp.tool()
async def compare_env_to_example(
    project_root: str,
    example_filename: str = ".env.example",
    env_filename: str = ".env",
) -> str:
    """Compare keys in .env.example with keys in .env under project_root.

    Reports variables documented in the example but missing from .env, variables set in .env
    but not listed in the example, duplicates, and empty placeholders in the example file.
    """
    try:
        root_example = resolve_under_root(project_root, example_filename)
        root_env = resolve_under_root(project_root, env_filename)
    except EnvAlignError as e:
        return json.dumps({"ok": False, "error": str(e)})

    ex_text = _read_text(root_example)
    if ex_text is None:
        return json.dumps(
            {
                "ok": False,
                "error": f"missing example file: {example_filename}",
                "resolved_path": str(root_example),
            }
        )

    env_text = _read_text(root_env)
    example_parsed = parse_dotenv_text(ex_text)
    env_parsed = parse_dotenv_text(env_text) if env_text is not None else None

    payload = {
        "ok": True,
        "project_root": str(Path(project_root).resolve()),
        "example_file": str(root_example),
        "env_file": str(root_env),
        "env_file_exists": env_text is not None,
        "comparison": compare_example_to_env(example_parsed, env_parsed),
    }
    return json.dumps(payload, indent=2)


@mcp.tool()
async def parse_env_example(
    project_root: str,
    example_filename: str = ".env.example",
) -> str:
    """List keys from .env.example with whether a non-empty default is set and inline # hints."""
    try:
        path = resolve_under_root(project_root, example_filename)
    except EnvAlignError as e:
        return json.dumps({"ok": False, "error": str(e)})

    text = _read_text(path)
    if text is None:
        return json.dumps(
            {
                "ok": False,
                "error": f"missing file: {example_filename}",
                "resolved_path": str(path),
            }
        )

    summary = parse_dotenv_text(text)
    rows = parse_dotenv_detailed(text)
    return json.dumps(
        {
            "ok": True,
            "resolved_path": str(path),
            "keys": rows,
            "duplicate_keys": summary.duplicate_keys,
            "key_count": len(summary.values),
        },
        indent=2,
    )


@mcp.tool()
async def mask_env_preview(
    project_root: str,
    env_filename: str = ".env",
    max_keys: int = 50,
) -> str:
    """Return env keys with masked values so logs and agent traces stay safe."""
    if max_keys < 1 or max_keys > 200:
        return json.dumps({"ok": False, "error": "max_keys must be between 1 and 200"})

    try:
        path = resolve_under_root(project_root, env_filename)
    except EnvAlignError as e:
        return json.dumps({"ok": False, "error": str(e)})

    text = _read_text(path)
    if text is None:
        return json.dumps(
            {
                "ok": True,
                "resolved_path": str(path),
                "exists": False,
                "preview": [],
            }
        )

    parsed = parse_dotenv_text(text)
    preview: list[dict[str, str]] = []
    for key in parsed.key_order[:max_keys]:
        preview.append({"key": key, "masked_value": mask_value(parsed.values.get(key, ""))})
    truncated = len(parsed.key_order) > max_keys
    return json.dumps(
        {
            "ok": True,
            "resolved_path": str(path),
            "exists": True,
            "preview": preview,
            "truncated": truncated,
            "total_keys": len(parsed.key_order),
            "duplicate_keys": parsed.duplicate_keys,
        },
        indent=2,
    )


if __name__ == "__main__":
    mcp.run(transport="stdio")
