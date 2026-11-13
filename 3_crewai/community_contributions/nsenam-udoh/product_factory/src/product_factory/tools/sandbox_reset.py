from contextlib import contextmanager
import os
from pathlib import Path
import re
import shutil
import stat
import subprocess


WORKSTREAM_ID_PATTERN = re.compile(r"^[a-z0-9][a-z0-9_-]{0,39}$")


def validate_workstream_id(workstream_id: str) -> str:
    if not WORKSTREAM_ID_PATTERN.fullmatch(workstream_id):
        raise ValueError(
            "Workstream id must match ^[a-z0-9][a-z0-9_-]{0,39}$"
        )
    return workstream_id


def workstream_root(workstream_id: str) -> Path:
    return Path.cwd() / "sandbox" / validate_workstream_id(workstream_id)


def workstream_lock_path(root: Path) -> Path:
    return root.with_name(f"{root.name}.lock")


def _lock_error(root: Path) -> RuntimeError:
    lock = workstream_lock_path(root)
    return RuntimeError(
        f"Workstream is locked by an active build: {lock}. If this is a stale "
        "lock, delete the lock file manually."
    )


@contextmanager
def workstream_lock(root: Path):
    lock = workstream_lock_path(root)
    lock.parent.mkdir(parents=True, exist_ok=True)
    try:
        lock.open("x", encoding="utf-8").close()
    except FileExistsError:
        raise _lock_error(root) from None
    try:
        yield
    finally:
        lock.unlink(missing_ok=True)


def _onexc(func, name, exc):
    del exc
    os.chmod(name, stat.S_IWRITE)
    path = Path(name)
    if os.path.islink(name) or path.is_symlink():
        os.unlink(name)
    elif path.is_dir() and os.name == "nt":
        result = subprocess.run(
            ["cmd", "/c", "rmdir", "/s", "/q", name],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        if result.returncode != 0 and path.exists():
            raise OSError(result.stderr or f"rmdir failed: {name}")
    elif path.is_dir():
        func(name)
    else:
        os.remove(name)


def _rmtree(path: Path) -> None:
    if not path.exists():
        return
    venv = path / ".venv"
    if venv.exists() and os.name == "nt":
        result = subprocess.run(
            ["cmd", "/c", "rmdir", "/s", "/q", str(venv)],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        if result.returncode != 0 and venv.exists():
            raise OSError(result.stderr or f"Failed to remove venv: {venv}")
    shutil.rmtree(path, onexc=_onexc)
    if path.exists():
        raise OSError(f"Failed to fully remove sandbox directory: {path}")


def _reset_workstream(root: Path) -> None:
    _rmtree(root)
    root.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        ["uv", "init", "--bare", "--no-workspace", "--python", "3.13"],
        cwd=root,
        check=True,
    )
    subprocess.run(["uv", "add", "gradio"], cwd=root, check=True)


def reset_workstream(root: Path) -> None:
    if workstream_lock_path(root).exists():
        raise _lock_error(root)
    _reset_workstream(root)
