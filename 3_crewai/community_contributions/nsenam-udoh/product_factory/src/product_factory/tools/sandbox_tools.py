import hashlib
import os
from pathlib import Path
import socket
import subprocess
import time
from urllib.request import urlopen
import uuid

from crewai.tools import tool


MAX_OUTPUT_CHARS = 8_000
MAX_READ_CHARS = 5_000
MAX_WRITE_CHARS = 200_000
WRITE_PREVIEW_CHARS = 4_000
# Cold Docker + uv + Gradio import for validators needs headroom; keep below
# agent max_execution_time so multiple validate/app-check cycles still fit.
RUN_TIMEOUT_SECONDS = 180
APP_CHECK_TIMEOUT_SECONDS = 120


def _sandbox_path(root: Path, filename: str) -> Path:
    resolved_root = root.resolve()
    candidate = (root / filename).resolve()
    if not candidate.is_relative_to(resolved_root):
        raise ValueError(f"Path escapes sandbox: {filename}")
    return candidate


def _is_link(path: Path) -> bool:
    if path.is_symlink():
        return True
    is_junction = getattr(path, "is_junction", None)
    return bool(is_junction and is_junction())


def _truncate(text: str, limit: int = MAX_OUTPUT_CHARS) -> str:
    if len(text) <= limit:
        return text
    footer = f"\n\n[Truncated: showing first {{shown}} of {len(text)} characters.]"
    shown = max(0, limit - len(footer.format(shown=0)) - 8)
    return text[:shown] + footer.format(shown=shown)


def make_sandbox_tools(root: Path) -> list:
    root = root.resolve()
    root.mkdir(parents=True, exist_ok=True)

    @tool("list_sandbox_files")
    def list_sandbox_files() -> str:
        """List regular files, pruning environments, caches, links, and junctions."""
        files = []
        walk_errors: list[OSError] = []
        try:
            for directory, dirnames, filenames in os.walk(
                root, followlinks=False, onerror=walk_errors.append
            ):
                current = Path(directory)
                dirnames[:] = [
                    name
                    for name in dirnames
                    if name not in {".venv", "__pycache__"}
                    and not _is_link(current / name)
                ]
                for name in filenames:
                    path = current / name
                    if not _is_link(path):
                        files.append(path.relative_to(root).as_posix())
            if walk_errors:
                return str(walk_errors[0])
            return "\n".join(sorted(files)) if files else "The sandbox is empty."
        except OSError as exc:
            return str(exc)

    @tool("read_sandbox_file")
    def read_sandbox_file(
        filename: str,
        start_line: int = 1,
        end_line: int | None = None,
    ) -> str:
        """Read UTF-8 text from this workstream. Prefer a short line range for
        signatures; full reads are capped to protect context."""
        try:
            path = _sandbox_path(root, filename)
            if not path.is_file():
                return f"No such file in the sandbox: {filename}"
            if start_line < 1:
                return "start_line must be >= 1."
            if end_line is not None and end_line < start_line:
                return "end_line must be >= start_line."
            lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
            selected = lines[start_line - 1 : end_line]
            full_read = start_line == 1 and end_line is None
            if not selected:
                if full_read:
                    return ""
                return (
                    f"No lines in range {start_line}-"
                    f"{end_line if end_line is not None else 'end'} "
                    f"({len(lines)} lines total)."
                )
            body = "".join(selected)
            if full_read:
                return _truncate(body, MAX_READ_CHARS)
            last_included = start_line + len(selected) - 1
            header = f"Lines {start_line}-{last_included} of {len(lines)}:\n"
            capped = _truncate(header + body, MAX_READ_CHARS)
            if len(header + body) > MAX_READ_CHARS and "[Truncated:" in capped:
                # Header line counts describe the requested slice; body may be shorter.
                return capped.replace(
                    header,
                    f"Lines {start_line}-{last_included} of {len(lines)} "
                    f"(output truncated to {MAX_READ_CHARS} characters):\n",
                    1,
                )
            return capped
        except (OSError, ValueError) as exc:
            return str(exc)

    @tool("write_sandbox_file")
    def write_sandbox_file(filename: str, content: str) -> str:
        """Write a UTF-8 text file inside this workstream, replacing it."""
        if len(content) > MAX_WRITE_CHARS:
            return f"Write rejected: content exceeds {MAX_WRITE_CHARS} characters."
        try:
            path = _sandbox_path(root, filename)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
            digest = hashlib.sha256(content.encode("utf-8")).hexdigest()
            return (
                f"Wrote {len(content)} characters to {filename}.\n"
                f"SHA256: {digest}\n"
                f"Preview (first {WRITE_PREVIEW_CHARS} characters):\n"
                f"{content[:WRITE_PREVIEW_CHARS]}"
            )
        except (OSError, ValueError) as exc:
            return str(exc)

    @tool("delete_sandbox_file")
    def delete_sandbox_file(filename: str) -> str:
        """Delete one file inside this workstream; never delete directories."""
        try:
            path = _sandbox_path(root, filename)
            if not path.exists():
                return f"No such file in the sandbox: {filename}"
            if not path.is_file():
                return f"Refusing to delete a non-file: {filename}"
            path.unlink()
            return f"Deleted sandbox file: {filename}"
        except (OSError, ValueError) as exc:
            return str(exc)

    @tool("run_sandbox_python")
    def run_sandbox_python(filename: str) -> str:
        """Run a workstream Python file in a resource-limited Docker container."""
        try:
            path = _sandbox_path(root, filename)
        except ValueError as exc:
            return str(exc)
        if not path.is_file():
            return f"No such file in the sandbox: {filename}"
        container_name = f"pf-{uuid.uuid4().hex}"
        relative_name = path.relative_to(root).as_posix()
        ran = f"Ran: uv run {relative_name}\n"
        command = [
            "docker", "run", "--rm", "--name", container_name,
            "--memory", "1g", "--cpus", "1", "--pids-limit", "256",
            "-e", "PYTHONIOENCODING=utf-8", "-e", "PYTHONUTF8=1",
            "-e", "GRADIO_ANALYTICS_ENABLED=False",
            "-v", f"{root}:/workspace", "-w", "/workspace",
            "ghcr.io/astral-sh/uv:python3.13-bookworm-slim",
            "uv", "run", relative_name,
        ]
        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=RUN_TIMEOUT_SECONDS,
            )
            return (
                f"{ran}Exit code: {result.returncode}\n\n--- stdout ---\n"
                f"{_truncate(result.stdout) or '(empty)'}\n\n--- stderr ---\n"
                f"{_truncate(result.stderr) or '(empty)'}"
            )
        except subprocess.TimeoutExpired as exc:
            subprocess.run(
                ["docker", "rm", "-f", container_name],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=30,
            )
            stdout = exc.stdout or ""
            stderr = exc.stderr or ""
            if isinstance(stdout, bytes):
                stdout = stdout.decode("utf-8", errors="replace")
            if isinstance(stderr, bytes):
                stderr = stderr.decode("utf-8", errors="replace")
            return (
                f"{ran}Exit code: timed out after {RUN_TIMEOUT_SECONDS} seconds\n"
                "Do NOT start a Gradio/web server with run_sandbox_python; use "
                "check_sandbox_app for app.py launch checks, and keep validators "
                "import-only (no demo.launch()).\n\n"
                f"--- stdout ---\n{_truncate(stdout) or '(empty)'}\n\n"
                f"--- stderr ---\n{_truncate(stderr) or '(empty)'}"
            )
        except OSError as exc:
            return (
                f"{ran}Exit code: error\n\n--- stdout ---\n(empty)\n\n"
                f"--- stderr ---\n{exc}"
            )

    @tool("check_sandbox_app")
    def check_sandbox_app() -> str:
        """Launch app.py in Docker and require an HTTP 200 response."""
        prefix = "App check: uv run app.py\n"
        if not (root / "app.py").is_file():
            return f"{prefix}FAILED\nNo such file in the sandbox: app.py"
        container_name = f"pf-{uuid.uuid4().hex}"
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.bind(("127.0.0.1", 0))
            port = sock.getsockname()[1]
        command = [
            "docker", "run", "--detach", "--name", container_name,
            "--memory", "1g", "--cpus", "1", "--pids-limit", "256",
            "-e", "PYTHONIOENCODING=utf-8", "-e", "PYTHONUTF8=1",
            "-e", "GRADIO_ANALYTICS_ENABLED=False",
            "-e", "GRADIO_SERVER_NAME=0.0.0.0", "-e", "GRADIO_SERVER_PORT=7860",
            "-p", f"127.0.0.1:{port}:7860",
            "-v", f"{root}:/workspace", "-w", "/workspace",
            "ghcr.io/astral-sh/uv:python3.13-bookworm-slim",
            "uv", "run", "app.py",
        ]
        try:
            try:
                started = subprocess.run(
                    command, capture_output=True, text=True, encoding="utf-8",
                    errors="replace", timeout=30,
                )
                if started.returncode != 0:
                    detail = (started.stderr or started.stdout or "").strip()
                    failure = f"Docker launch failed. {detail}".rstrip()
                else:
                    deadline = time.monotonic() + APP_CHECK_TIMEOUT_SECONDS
                    while time.monotonic() < deadline:
                        state = subprocess.run(
                            [
                                "docker", "inspect", "-f", "{{.State.Running}}",
                                container_name,
                            ],
                            capture_output=True, text=True, encoding="utf-8",
                            errors="replace", timeout=30,
                        )
                        if state.returncode == 0 and state.stdout.strip() == "false":
                            failure = "App exited before serving HTTP 200."
                            break
                        try:
                            with urlopen(
                                f"http://127.0.0.1:{port}/", timeout=2
                            ) as response:
                                if response.status == 200:
                                    return f"{prefix}HTTP 200"
                        except OSError:
                            pass
                        time.sleep(1)
                    else:
                        failure = (
                            "App did not return HTTP 200 within "
                            f"{APP_CHECK_TIMEOUT_SECONDS} seconds."
                        )
            except (OSError, subprocess.TimeoutExpired) as exc:
                failure = str(exc)
            try:
                logged = subprocess.run(
                    ["docker", "logs", container_name],
                    capture_output=True, text=True, encoding="utf-8",
                    errors="replace", timeout=30,
                )
                output = "\n".join(
                    part for part in (logged.stdout, logged.stderr) if part
                )
                log_tail = _truncate("\n".join(output.splitlines()[-40:]))
            except (OSError, subprocess.TimeoutExpired) as exc:
                log_tail = str(exc)
            return (
                f"{prefix}FAILED\n{failure}\nContainer logs (last lines):\n"
                f"{log_tail or '(no container logs)'}"
            )
        finally:
            try:
                subprocess.run(
                    ["docker", "rm", "-f", container_name],
                    capture_output=True, text=True, encoding="utf-8",
                    errors="replace", timeout=30,
                )
            except (OSError, subprocess.TimeoutExpired):
                pass

    tools = [
        list_sandbox_files,
        read_sandbox_file,
        write_sandbox_file,
        delete_sandbox_file,
        run_sandbox_python,
        check_sandbox_app,
    ]
    for sandbox_tool in tools:
        sandbox_tool.cache_function = lambda *args, **kwargs: False
    return tools
