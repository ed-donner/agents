"""Windows + Jupyter fix for MCPServerStdio (streams without fileno). Same idea as windows_no_wsl/winpatch.py."""

from __future__ import annotations

import io
import os
import platform
import subprocess
from typing import Any, Tuple

STREAM_NAMES = ("stdin", "stdout", "stderr")
NPX_PREFIX = "npx"


def _has_valid_fileno(stream) -> bool:
    if not hasattr(stream, "fileno"):
        return False
    try:
        stream.fileno()
        return True
    except (io.UnsupportedOperation, AttributeError):
        return False


def _replace_invalid_streams(kwargs: dict) -> None:
    for stream_name in STREAM_NAMES:
        stream = kwargs.get(stream_name)
        if stream is not None and not _has_valid_fileno(stream):
            kwargs[stream_name] = subprocess.PIPE


def _is_npx_command(cmd: Any) -> bool:
    return isinstance(cmd, str) and os.path.basename(cmd).startswith(NPX_PREFIX)


def _wrap_npx_command(args: Tuple) -> Tuple:
    if not args or not isinstance(args[0], list) or not args[0]:
        return args
    if _is_npx_command(args[0][0]):
        original_cmd = args[0]
        wrapped_cmd = ["cmd", "/c"] + args[0]
        print("Wrapping npx with cmd /c")
        print("  Before:", original_cmd)
        print("  After:", wrapped_cmd)
        return (wrapped_cmd,) + args[1:]
    return args


class WindowsPatchedPopen(subprocess.Popen):
    def __init__(self, *args, **kwargs):
        _replace_invalid_streams(kwargs)
        args = _wrap_npx_command(args)
        super().__init__(*args, **kwargs)


def winpatch_mcpserver_stdio() -> None:
    """Patch subprocess.Popen so MCPServerStdio works in Jupyter on Windows."""
    print(f"Platform: {platform.system()}")
    if platform.system() != "Windows":
        return
    subprocess.Popen = WindowsPatchedPopen
    print("Applied Windows fix for MCPServerStdio (stdio pipes).")
