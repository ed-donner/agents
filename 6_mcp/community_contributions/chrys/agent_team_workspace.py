
from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any

from agents import Runner
from agents.items import (
    HandoffCallItem,
    HandoffOutputItem,
    MessageOutputItem,
    ReasoningItem,
    ToolCallItem,
    ToolCallOutputItem,
)
from agents.stream_events import AgentUpdatedStreamEvent, RawResponsesStreamEvent, RunItemStreamEvent


def sanitize_name(name: str) -> str:
    return "".join(c if c.isalnum() else "_" for c in (name or "agent").lower())


def extract_json_object_text(raw: str) -> str:
    """Strip optional ``` / ```json fences from a model message."""
    s = (raw or "").strip()
    if not s.startswith("```"):
        return s
    lines = s.splitlines()
    if not lines:
        return s
    lines = lines[1:]
    while lines and lines[-1].strip().startswith("```"):
        lines = lines[:-1]
    return "\n".join(lines).strip()


_TOOL_ID_ALIASES: dict[str, str] = {
    "alphabetavantage": "alphavantage",
    "pushoot": "pushover",
    "resres": "resend",
}


def normalize_completion_state_json(obj: Any) -> Any:
    """Unwrap IDE-style {completionState, entries/items/value} trees into plain JSON values."""
    if obj is None or isinstance(obj, (bool, int, float)):
        return obj
    if isinstance(obj, str):
        ss = obj.strip()
        if len(ss) >= 2 and ss[0] in "[{" and ss[-1] in "]}":
            try:
                return normalize_completion_state_json(json.loads(ss))
            except json.JSONDecodeError:
                pass
        return obj
    if isinstance(obj, list):
        return [normalize_completion_state_json(x) for x in obj]
    if not isinstance(obj, dict):
        return obj
    if isinstance(obj.get("entries"), list):
        out: dict[str, Any] = {}
        for pair in obj["entries"]:
            if isinstance(pair, list) and len(pair) >= 2 and isinstance(pair[0], str):
                out[pair[0]] = normalize_completion_state_json(pair[1])
        return out
    if isinstance(obj.get("items"), list):
        return [normalize_completion_state_json(x) for x in obj["items"]]
    if (
        "value" in obj
        and "completionState" in obj
        and "entries" not in obj
        and "items" not in obj
    ):
        return normalize_completion_state_json(obj["value"])
    return {str(k): normalize_completion_state_json(v) for k, v in obj.items()}


def dedupe_tool_ids(tools: Any) -> list[str]:
    if not isinstance(tools, list):
        return []
    seen: list[str] = []
    for t in tools:
        if isinstance(t, dict) and "value" in t:
            t = t.get("value")
        if not isinstance(t, str):
            t = str(t)
        x = t.strip().lower().replace(" ", "_").replace("-", "_")
        x = _TOOL_ID_ALIASES.get(x, x)
        if x and x not in seen:
            seen.append(x)
    return seen


def coerce_team_dict_for_teamspec(data: Any) -> dict[str, Any]:
    """Parse/normalize team JSON from models that double-encode or emit completionState trees."""
    if isinstance(data, str):
        data = json.loads(data)
    if not isinstance(data, dict):
        raise TypeError("Team JSON must be a JSON object at the root")
    data = normalize_completion_state_json(data)
    if not isinstance(data, dict):
        raise TypeError("After normalization, team root must be an object")

    m = data.get("manager")
    if isinstance(m, str):
        try:
            data["manager"] = json.loads(m)
        except json.JSONDecodeError:
            data["manager"] = None
    data["manager"] = normalize_completion_state_json(data.get("manager"))

    spec = data.get("specialists")
    if isinstance(spec, str):
        try:
            data["specialists"] = json.loads(spec)
        except json.JSONDecodeError:
            data["specialists"] = []
    if not isinstance(data.get("specialists"), list):
        data["specialists"] = []
    fixed_specs: list[dict[str, Any]] = []
    for s in data["specialists"]:
        if isinstance(s, str):
            try:
                s = json.loads(s)
            except json.JSONDecodeError:
                continue
        s = normalize_completion_state_json(s)
        if isinstance(s, dict):
            fixed_specs.append(s)
    data["specialists"] = fixed_specs

    sc = data.get("success_criteria")
    if isinstance(sc, str):
        try:
            data["success_criteria"] = json.loads(sc)
        except json.JSONDecodeError:
            data["success_criteria"] = [sc]
    if not isinstance(data.get("success_criteria"), list):
        v = data.get("success_criteria")
        data["success_criteria"] = [] if v is None else [str(v)]

    def fix_agent(a: Any) -> dict[str, Any]:
        if not isinstance(a, dict):
            return {}
        d = dict(a)
        d["tools"] = dedupe_tool_ids(d.get("tools"))
        if not isinstance(d.get("mcp_servers"), list):
            d["mcp_servers"] = []
        d.setdefault("handoff_description", "")
        return d

    if isinstance(data.get("manager"), dict):
        data["manager"] = fix_agent(data["manager"])
    data["specialists"] = [fix_agent(s) for s in data["specialists"]]
    return data


def ensure_project_layout(
    *,
    generated_dir: str,
    manager_name: str,
    primary_language: str = "python",
) -> Path:
    """Create `project/` under the generated team with language-appropriate src/tests skeleton."""
    base = Path(generated_dir)
    proj = base / "project"
    proj.mkdir(parents=True, exist_ok=True)
    lang = (primary_language or "python").strip().lower()
    readme = proj / "README.md"
    if not readme.exists():
        readme.write_text(
            "# Project workspace\n\n"
            f"Primary language: **{lang}**.\n\n"
            "When emitting code, use a markdown fence whose **first line** is either:\n"
            "- `# file: src/...` or `# file: tests/...` (Python-style), or\n"
            "- `// file: src/...` (TS/JS)\n\n"
            "Paths are relative to this `project/` folder. Tests live under `tests/`.\n",
            encoding="utf-8",
        )
    if lang in ("python", "py"):
        pkg = sanitize_name(manager_name) or "app"
        if pkg and pkg[0].isdigit():
            pkg = "pkg_" + pkg
        (proj / "src" / pkg).mkdir(parents=True, exist_ok=True)
        init_py = proj / "src" / pkg / "__init__.py"
        if not init_py.exists():
            init_py.write_text(
                '"""Package for implementations produced by agent runs."""\n',
                encoding="utf-8",
            )
        (proj / "tests").mkdir(exist_ok=True)
        tp = proj / "tests" / "test_placeholder.py"
        if not tp.exists():
            tp.write_text(
                '"""Replace with real tests once features exist."""\n\n'
                "def test_placeholder() -> None:\n"
                "    assert True\n",
                encoding="utf-8",
            )
        pyt = proj / "pyproject.toml"
        if not pyt.exists():
            pyt.write_text(
                f'[project]\nname = "{pkg}-workspace"\nversion = "0.1.0"\n'
                'requires-python = ">=3.11"\n\n[tool.pytest.ini_options]\ntestpaths = ["tests"]\n',
                encoding="utf-8",
            )
    elif lang in ("typescript", "ts", "javascript", "js"):
        (proj / "src").mkdir(parents=True, exist_ok=True)
        (proj / "tests").mkdir(exist_ok=True)
        pkgj = proj / "package.json"
        if not pkgj.exists():
            pkgj.write_text(
                "{\n  \"name\": \"generated-workspace\",\n  \"version\": \"0.1.0\",\n"
                '  "scripts": { "test": "echo \\"Add jest/vitest\\"" }\n}\n',
                encoding="utf-8",
            )
        idx = proj / "src" / "index.ts"
        if not idx.exists():
            idx.write_text("// Add modules under src/\nexport {};\n", encoding="utf-8")
    else:
        (proj / "src").mkdir(exist_ok=True)
        (proj / "tests").mkdir(exist_ok=True)
    return proj


_FILE_FIRST_LINE = re.compile(
    r"^(?:#\s*(?:file|path)\s*:\s*|//\s*(?:file|path)\s*:\s*|(?:File|PATH)\s*:\s*)(.+)$",
    re.IGNORECASE,
)


def extract_and_write_project_files(project_root: Path, output: str) -> list[str]:
    """Parse fenced blocks with a file path on the line after the opening fence; write under project_root."""
    written: list[str] = []
    root = project_root.resolve()
    block = re.compile(r"```(?:[\w.+-]+)?\s*\n([^\n]+)\n([\s\S]*?)```", re.MULTILINE)
    for m in block.finditer(output):
        first_line, body = m.group(1).strip(), m.group(2).rstrip()
        fm = _FILE_FIRST_LINE.match(first_line)
        if not fm:
            continue
        rel = fm.group(1).strip().strip("`").strip("\"'")
        rel = rel.replace("\\", "/").lstrip("./")
        if ".." in rel or rel.startswith("/"):
            continue
        if rel.startswith("project/"):
            rel = rel[len("project/") :]
        target = (root / rel).resolve()
        try:
            target.relative_to(root)
        except ValueError:
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(body.lstrip("\n"), encoding="utf-8")
        written.append(rel)
    return written


def _message_text(msg: Any) -> str:
    parts: list[str] = []
    for part in getattr(msg, "content", []) or []:
        ptype = getattr(part, "type", None)
        if ptype == "output_text":
            parts.append(getattr(part, "text", "") or "")
        elif hasattr(part, "text"):
            parts.append(str(part.text))
    return "\n".join(parts).strip()


async def run_manager_streamed_collect(manager: Any, run_task: str) -> tuple[Any, list[dict[str, Any]], str]:
    """Run with Runner.run_streamed; return (final_output, timeline_json, interactions_markdown)."""
    timeline: list[dict[str, Any]] = []
    md_lines: list[str] = []
    stream = Runner.run_streamed(manager, run_task)
    async for event in stream.stream_events():
        if isinstance(event, RawResponsesStreamEvent):
            continue
        if isinstance(event, AgentUpdatedStreamEvent):
            name = event.new_agent.name
            timeline.append({"type": "agent_active", "agent": name})
            md_lines.append(f"### Active agent: **{name}**\n")
            continue
        if isinstance(event, RunItemStreamEvent):
            item = event.item
            agent_name = getattr(item.agent, "name", "?")
            if isinstance(item, ReasoningItem):
                ri = item.raw_item
                chunks: list[str] = []
                if getattr(ri, "summary", None):
                    chunks.append(str(ri.summary))
                c = getattr(ri, "content", None)
                if c:
                    chunks.append(str(c)[:4000])
                text = "\n".join(chunks) or "(reasoning)"
                timeline.append(
                    {"type": "reasoning", "agent": agent_name, "text": text[:8000]}
                )
                clip = text[:2000] + ("…" if len(text) > 2000 else "")
                md_lines.append(f"#### Reasoning — {agent_name}\n\n{clip}\n")
            elif isinstance(item, ToolCallItem):
                ri = item.raw_item
                tname = getattr(ri, "name", "tool")
                entry: dict[str, Any] = {
                    "type": "tool_call",
                    "agent": agent_name,
                    "tool": tname,
                }
                srv = getattr(ri, "server_label", None)
                if srv:
                    entry["mcp_server"] = srv
                args = getattr(ri, "arguments", None)
                if args is not None:
                    entry["arguments"] = str(args)[:8000]
                timeline.append(entry)
                extra = f" (MCP server: `{srv}`)" if srv else ""
                md_lines.append(f"- **{agent_name}** calls tool `{tname}`{extra}\n")
            elif isinstance(item, ToolCallOutputItem):
                prev = str(item.output)[:4000]
                timeline.append(
                    {"type": "tool_output", "agent": agent_name, "preview": prev}
                )
                md_lines.append(
                    f"  - output preview: `{prev[:280]}{'…' if len(prev) > 280 else ''}`\n"
                )
            elif isinstance(item, HandoffCallItem):
                ri = item.raw_item
                tname = getattr(ri, "name", "handoff")
                timeline.append(
                    {"type": "handoff_call", "agent": agent_name, "via": tname}
                )
                md_lines.append(f"- **{agent_name}** requests handoff (`{tname}`)\n")
            elif isinstance(item, HandoffOutputItem):
                timeline.append(
                    {
                        "type": "handoff",
                        "from": item.source_agent.name,
                        "to": item.target_agent.name,
                    }
                )
                md_lines.append(
                    f"#### Handoff **{item.source_agent.name}** → **{item.target_agent.name}**\n"
                )
            elif isinstance(item, MessageOutputItem):
                blob = _message_text(item.raw_item)
                if blob:
                    prev = blob[:1200]
                    timeline.append(
                        {
                            "type": "assistant_message",
                            "agent": agent_name,
                            "preview": prev,
                        }
                    )
                    md_lines.append(
                        f"#### Message — {agent_name}\n\n{prev}"
                        f"{'…' if len(blob) > 1200 else ''}\n"
                    )
    return stream.final_output, timeline, "\n".join(md_lines)


def save_run_bundle(
    base_dir: Path,
    *,
    task: str,
    output: str,
    evaluation: dict[str, Any],
    interactions_md: str,
    timeline: list[dict[str, Any]],
    extracted_files: list[str],
) -> dict[str, str]:
    """Write run markdown, evaluation JSON, interaction log + JSON, latest_run.md."""
    runs = base_dir / "runs"
    runs.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    md = runs / f"run_{ts}.md"
    evpath = runs / f"run_{ts}.evaluation.json"
    i_md = runs / f"run_{ts}_interactions.md"
    i_js = runs / f"run_{ts}_interactions.json"
    ext_note = (
        "\n".join(f"- `{p}`" for p in extracted_files)
        if extracted_files
        else "_No `# file:` blocks extracted — see final output for copy-paste artifacts._"
    )
    body = (
        f"# Team run {ts}\n\n## Task\n\n{task}\n\n## Model output\n\n{output}\n\n"
        f"## Files written under project/\n\n{ext_note}\n\n"
        f"## Agent interactions\n\nSee **`{i_md.name}`** and **`{i_js.name}`** for the full trace "
        f"(tools, handoffs, reasoning).\n\n"
        f"## Evaluation (JSON)\n\n```json\n"
        f"{json.dumps(evaluation, indent=2, ensure_ascii=False)}\n```\n"
    )
    md.write_text(body, encoding="utf-8")
    evpath.write_text(
        json.dumps(evaluation, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    i_md.write_text(
        f"# Agent interaction trace — {ts}\n\n{interactions_md}\n", encoding="utf-8"
    )
    i_js.write_text(json.dumps(timeline, indent=2, ensure_ascii=False), encoding="utf-8")
    latest = runs / "latest_run.md"
    latest.write_text(body, encoding="utf-8")
    return {
        "markdown": str(md),
        "evaluation_json": str(evpath),
        "interactions_md": str(i_md),
        "interactions_json": str(i_js),
        "latest": str(latest),
    }
