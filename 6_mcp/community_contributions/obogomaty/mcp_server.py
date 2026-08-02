import sys
import shutil
from pathlib import Path
from datetime import datetime, timedelta

print("[DEBUG] mcp_server.py starting...")
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("file_organizer")

def _human_size(b):
    for u in ["B", "KB", "MB", "GB", "TB"]:
        if b < 1024:
            return f"{b:.1f} {u}"
        b /= 1024
    return f"{b:.1f} PB"

def _safe_size(path):
    try:
        if path.is_file():
            return path.stat().st_size
        total = 0
        for f in path.rglob("*"):
            if f.is_file():
                try:
                    total += f.stat().st_size
                except OSError:
                    pass
        return total
    except OSError:
        return 0

@mcp.tool()
async def list_files(folder_path: str) -> str:
    p = Path(folder_path)
    if not p.is_dir():
        return f"Error: '{folder_path}' is not a valid directory."
    lines = []
    try:
        for item in sorted(p.iterdir()):
            try:
                sz = _safe_size(item)
                kind = "DIR" if item.is_dir() else "FILE"
                lines.append(f"{kind:<5} {_human_size(sz):>10}  {item.name}")
            except OSError:
                lines.append(f"???   {'N/A':>10}  {item.name}")
    except PermissionError:
        return f"Error: Permission denied for '{folder_path}'."
    return "\n".join(lines) if lines else "Folder is empty."

@mcp.tool()
async def create_folder(folder_path: str) -> str:
    p = Path(folder_path)
    if p.exists():
        return f"Already exists: {folder_path}"
    p.mkdir(parents=True, exist_ok=True)
    return f"Created: {folder_path}"

@mcp.tool()
async def move_file(source: str, destination_folder: str) -> str:
    src = Path(source)
    dst = Path(destination_folder)
    if not src.exists():
        return f"Error: '{source}' not found."
    dst.mkdir(parents=True, exist_ok=True)
    target = dst / src.name
    if target.exists():
        return f"Error: '{target}' already exists. Rename or skip."
    shutil.move(str(src), str(target))
    return f"Moved: {src.name} -> {destination_folder}"

@mcp.tool()
async def get_sizes(folder_path: str) -> str:
    p = Path(folder_path)
    if not p.is_dir():
        return f"Error: '{folder_path}' is not a valid directory."
    items = []
    for item in p.iterdir():
        try:
            sz = _safe_size(item)
            items.append((sz, "DIR" if item.is_dir() else "FILE", item.name))
        except OSError:
            pass
    items.sort(reverse=True)
    lines = [f"{_human_size(s):>10}  {k:<5} {n}" for s, k, n in items]
    total = sum(s for s, _, _ in items)
    lines.append(f"\nTotal: {_human_size(total)}")
    return "\n".join(lines)

@mcp.tool()
async def find_large_files(folder_path: str, top_n: int = 20) -> str:
    files = []
    for f in Path(folder_path).rglob("*"):
        if f.is_file():
            try:
                files.append((f.stat().st_size, str(f)))
            except OSError:
                pass
    files.sort(reverse=True)
    lines = [f"{_human_size(s):>10}  {p}" for s, p in files[:top_n]]
    return "\n".join(lines) if lines else "No files found."

@mcp.tool()
async def find_old_files(folder_path: str, days: int = 90) -> str:
    cutoff = datetime.now() - timedelta(days=days)
    old = []
    for f in Path(folder_path).rglob("*"):
        if f.is_file():
            try:
                mt = datetime.fromtimestamp(f.stat().st_mtime)
                if mt < cutoff:
                    old.append((mt, f.stat().st_size, str(f)))
            except OSError:
                pass
    old.sort()
    if not old:
        return f"No files older than {days} days found."
    lines = [f"{m.strftime('%Y-%m-%d')}  {_human_size(s):>10}  {p}" for m, s, p in old[:50]]
    if len(old) > 50:
        lines.append(f"...and {len(old) - 50} more")
    return "\n".join(lines)

@mcp.tool()
async def group_by_extension(folder_path: str) -> str:
    groups = {}
    for f in Path(folder_path).iterdir():
        if f.is_file():
            try:
                ext = f.suffix.lower() or "(no ext)"
                groups.setdefault(ext, []).append((f.stat().st_size, f.name))
            except OSError:
                pass
    if not groups:
        return "No files found."
    lines = []
    for ext in sorted(groups):
        files = sorted(groups[ext], reverse=True)
        total = sum(s for s, _ in files)
        lines.append(f"\n{ext}  —  {len(files)} files, {_human_size(total)}")
        for s, n in files:
            lines.append(f"  {_human_size(s):>10}  {n}")
    return "\n".join(lines)

@mcp.tool()
async def organize_by_type(folder_path: str) -> str:
    CATEGORIES = {
        "Images": {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".svg", ".webp", ".ico"},
        "Documents": {".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx", ".txt", ".rtf", ".csv"},
        "Videos": {".mp4", ".mkv", ".avi", ".mov", ".wmv", ".webm"},
        "Audio": {".mp3", ".wav", ".flac", ".aac", ".ogg", ".m4a"},
        "Archives": {".zip", ".rar", ".7z", ".tar", ".gz"},
        "Code": {".py", ".js", ".ts", ".html", ".css", ".java", ".json", ".xml", ".yaml", ".yml"},
        "Installers": {".exe", ".msi", ".bat", ".cmd"},
    }
    ext_map = {e: c for c, exts in CATEGORIES.items() for e in exts}

    p = Path(folder_path)
    if not p.is_dir():
        return f"Error: '{folder_path}' is not a valid directory."

    moved, skipped = [], []
    for f in list(p.iterdir()):
        if not f.is_file():
            continue
        cat = ext_map.get(f.suffix.lower(), "Other")
        dest = p / cat
        dest.mkdir(exist_ok=True)
        target = dest / f.name
        if target.exists():
            skipped.append(f"  Skipped (exists): {f.name}")
            continue
        try:
            shutil.move(str(f), str(target))
            moved.append(f"  {f.name} -> {cat}/")
        except OSError as e:
            skipped.append(f"  Error: {f.name} — {e}")

    parts = []
    if moved:
        parts.append(f"Moved {len(moved)} files:\n" + "\n".join(moved))
    if skipped:
        parts.append(f"Skipped {len(skipped)}:\n" + "\n".join(skipped))
    return "\n\n".join(parts) if parts else "No files to organize."

def run():
    print("[DEBUG] MCP server about to run...")
    mcp.run(transport="stdio")

if __name__ == "__main__":
    print("[DEBUG] __main__ entrypoint reached.")
    run()

