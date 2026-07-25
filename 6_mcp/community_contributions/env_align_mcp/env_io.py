"""Local .env / .env.example parsing and comparison (no secrets sent to models by default)."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path


class EnvAlignError(ValueError):
    pass


def resolve_under_root(project_root: str, *relative_parts: str) -> Path:
    root = Path(project_root).expanduser().resolve()
    if not root.is_dir():
        raise EnvAlignError(f"project_root is not a directory: {root}")
    candidate = (root.joinpath(*relative_parts)).resolve()
    try:
        candidate.relative_to(root)
    except ValueError as exc:
        raise EnvAlignError("path escapes project_root") from exc
    return candidate


@dataclass
class ParsedEnvFile:
    """Last assignment wins per key; tracks order and duplicate key names."""

    values: dict[str, str] = field(default_factory=dict)
    key_order: list[str] = field(default_factory=list)
    duplicate_keys: list[str] = field(default_factory=list)


_LINE_RE = re.compile(
    r"^(?P<export>export\s+)?(?P<key>[A-Za-z_][A-Za-z0-9_]*)\s*=\s*(?P<rest>.*)$"
)


def parse_dotenv_text(text: str) -> ParsedEnvFile:
    """Parse a dotenv-style file (common cases; not a full shell parser)."""
    values: dict[str, str] = {}
    key_order: list[str] = []
    seen: set[str] = set()
    duplicate_keys: list[str] = []

    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        m = _LINE_RE.match(line)
        if not m:
            continue
        key = m.group("key")
        rest = m.group("rest").strip()
        value, inline_hint = _split_value_and_comment(rest)
        if key in values and key not in duplicate_keys:
            duplicate_keys.append(key)
        if key not in seen:
            key_order.append(key)
            seen.add(key)
        values[key] = value

    return ParsedEnvFile(
        values=values,
        key_order=key_order,
        duplicate_keys=sorted(set(duplicate_keys)),
    )


def _split_value_and_comment(rest: str) -> tuple[str, str | None]:
    if not rest:
        return "", None
    if rest.startswith('"'):
        end = _closing_quote(rest, '"')
        if end == -1:
            return rest, None
        val = _unescape(rest[1:end])
        tail = rest[end + 1 :].strip()
        hint = _comment_after(tail)
        return val, hint
    if rest.startswith("'"):
        end = rest.find("'", 1)
        if end == -1:
            return rest, None
        val = rest[1:end]
        tail = rest[end + 1 :].strip()
        hint = _comment_after(tail)
        return val, hint
    if "#" in rest:
        before, _, after = rest.partition("#")
        return before.strip(), after.strip() or None
    return rest.strip(), None


def _closing_quote(s: str, q: str) -> int:
    i = 1
    while i < len(s):
        if s[i] == "\\" and i + 1 < len(s):
            i += 2
            continue
        if s[i] == q:
            return i
        i += 1
    return -1


def _unescape(s: str) -> str:
    out: list[str] = []
    i = 0
    while i < len(s):
        if s[i] == "\\" and i + 1 < len(s):
            out.append(s[i + 1])
            i += 2
            continue
        out.append(s[i])
        i += 1
    return "".join(out)


def _comment_after(tail: str) -> str | None:
    if not tail:
        return None
    if tail.startswith("#"):
        return tail[1:].strip() or None
    return None


def parse_dotenv_detailed(text: str) -> list[dict[str, str | bool | None]]:
    """Row-level view for documentation: key, whether a value is set, inline hint."""
    rows: list[dict[str, str | bool | None]] = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        m = _LINE_RE.match(line)
        if not m:
            continue
        key = m.group("key")
        rest = m.group("rest").strip()
        value, hint = _split_value_and_comment(rest)
        rows.append(
            {
                "key": key,
                "has_value": bool(value),
                "inline_hint": hint,
            }
        )
    return rows


def mask_value(value: str, visible: int = 2) -> str:
    if not value:
        return "(empty)"
    if len(value) <= visible * 2:
        return "*" * len(value)
    return f"{value[:visible]}...{value[-visible:]} ({len(value)} chars)"


def compare_example_to_env(
    example: ParsedEnvFile, env: ParsedEnvFile | None
) -> dict[str, object]:
    ex_keys = set(example.values.keys())
    env_keys = set(env.values.keys()) if env else set()
    missing_in_env = sorted(ex_keys - env_keys)
    not_in_example = sorted(env_keys - ex_keys)
    in_both = sorted(ex_keys & env_keys)
    empty_in_example = sorted(k for k in ex_keys if not example.values.get(k, "").strip())
    return {
        "missing_in_env": missing_in_env,
        "set_but_not_documented_in_example": not_in_example,
        "present_in_both": in_both,
        "empty_placeholder_in_example": empty_in_example,
        "duplicate_keys_in_example": example.duplicate_keys,
        "duplicate_keys_in_env": env.duplicate_keys if env else [],
    }
