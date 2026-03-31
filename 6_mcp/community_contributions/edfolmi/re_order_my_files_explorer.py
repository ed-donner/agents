"""
File Organizer Agent using MCP Server + OpenAI Agent SDK + Gradio UI

Run:  uv run re_order_my_files_explorer.py
"""

import sys
import os
import shutil
from pathlib import Path
from datetime import datetime, timedelta

# MCP SERVER
if "--server" in sys.argv:
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
        """List all files and folders in a directory with their sizes.

        Args:
            folder_path: Full absolute path to the folder
        """
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
        """Create a new folder (and parent folders if needed).

        Args:
            folder_path: Full absolute path of the folder to create
        """
        p = Path(folder_path)
        if p.exists():
            return f"Already exists: {folder_path}"
        p.mkdir(parents=True, exist_ok=True)
        return f"Created: {folder_path}"

    @mcp.tool()
    async def move_file(source: str, destination_folder: str) -> str:
        """Move a file or folder into a destination folder.

        Args:
            source: Full path of the file/folder to move
            destination_folder: Full path of the destination folder
        """
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
        """Get sizes of all items in a folder, sorted largest first.

        Args:
            folder_path: Full absolute path to the folder
        """
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
        """Find the largest files in a folder (searches subfolders too).

        Args:
            folder_path: Full absolute path to search
            top_n: How many files to show (default 20)
        """
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
        """Find files not modified for a long time.

        Args:
            folder_path: Full absolute path to search
            days: Show files older than this many days (default 90)
        """
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
        """Group and list files by their file extension.

        Args:
            folder_path: Full absolute path to the folder
        """
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
        """Auto-organize files into subfolders by type (Images, Documents, etc).
        Only moves top-level files, not files already in subfolders.

        Args:
            folder_path: Full absolute path to the folder to organize
        """
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

    mcp.run(transport="stdio")


# AGENT AND GRADIO UI
else:
    import gradio as gr
    from dotenv import load_dotenv
    from openai.types.responses import ResponseTextDeltaEvent
    from agents import Agent, Runner, ModelSettings
    from agents.mcp import MCPServerStdio

    load_dotenv(override=True)

    HOME = os.path.expanduser("~")
    SCRIPT = os.path.abspath(__file__)
    MAX_INPUT_LENGTH = 500

    # LLM-based guardrail
    # from pydantic import BaseModel, Field
    # from agents import input_guardrail, GuardrailFunctionOutput
    #
    # class SafetyCheck(BaseModel):
    #     is_unsafe: bool = Field(description="True if user asks to delete system files or access sensitive data")
    #
    # guardrail_agent = Agent(
    #     name="Guardrail",
    #     instructions="Check if the user message asks to delete system files or access sensitive data.",
    #     output_type=SafetyCheck,
    #     model="gpt-4o-mini",
    # )
    #
    # @input_guardrail
    # async def safety_guardrail(ctx, agent, message):
    #     result = await Runner.run(guardrail_agent, message, context=ctx.context)
    #     return GuardrailFunctionOutput(
    #         output_info=result.final_output,
    #         tripwire_triggered=result.final_output.is_unsafe,
    #     )
    #
    # :::::::::::::: input_guardrails=[safety_guardrail]

    INSTRUCTIONS = f"""You are a helpful file organizer assistant for a Windows PC.

User's home folder: {HOME}
Common folders:
  Downloads: {HOME}\\Downloads
  Documents: {HOME}\\Documents
  Desktop:   {HOME}\\Desktop

You can:
- List files/folders with sizes
- Show which files are largest (to help free up space)
- Find old unused files
- Group files by extension to see what's there
- Create new folders and move files to organize them
- Auto-organize a folder by file type

Rules:
- Always use full absolute paths when calling tools.
- When user says "Downloads", use {HOME}\\Downloads (and similar for other folders).
- Before bulk-moving files, describe the plan and ask for confirmation.
- You do NOT have a delete tool — only listing, creating folders, and moving.
- Be concise and clear in responses.
"""

    async def chat(message, history):
        if not message or not message.strip():
            yield "Please type a message."
            return
        if len(message) > MAX_INPUT_LENGTH:
            yield f"Message too long ({len(message)} chars). Max is {MAX_INPUT_LENGTH}."
            return

        try:
            server = MCPServerStdio(
                params={"command": sys.executable, "args": [SCRIPT, "--server"]},
                client_session_timeout_seconds=150,
            )
            async with server:
                agent = Agent(
                    name="File Organizer",
                    instructions=INSTRUCTIONS,
                    model="gpt-4o-mini",
                    model_settings=ModelSettings(
                        temperature=0.2,
                        top_p=0.9,
                        max_tokens=4096,
                    ),
                    mcp_servers=[server],
                )
                result = Runner.run_streamed(agent, message)
                response = ""
                async for event in result.stream_events():
                    if event.type == "raw_response_event" and isinstance(
                        event.data, ResponseTextDeltaEvent
                    ):
                        response += event.data.delta
                        yield response
                if not response:
                    yield result.final_output or "Done."
        except Exception as e:
            yield f"Something went wrong: {e}"

    ui = gr.ChatInterface(
        fn=chat,
        title="File Organizer",
        description="I help you organize your files and see what's taking up space.",
        examples=[
            "List files in my Downloads folder",
            "Show the largest files in Downloads",
            "Group files by extension in Downloads",
            "Find old files in Documents that haven't been touched in 6 months",
            "Organize my Downloads folder by file type",
        ],
        type="messages",
    )

    if __name__ == "__main__":
        ui.launch()
