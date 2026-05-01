import io
import os
import platform
import subprocess
from typing import Any, Tuple


STREAM_NAMES = ('stdin', 'stdout', 'stderr')
NPX_PREFIX = 'npx'


def _has_valid_fileno(stream) -> bool:
    """Check if a stream has a working fileno() method."""
    if not hasattr(stream, 'fileno'):
        return False
    try:
        stream.fileno()
        return True
    except (io.UnsupportedOperation, AttributeError):
        return False


def _replace_invalid_streams(kwargs: dict) -> None:
    """Replace streams without fileno() support with subprocess.PIPE."""
    for stream_name in STREAM_NAMES:
        stream = kwargs.get(stream_name)
        if stream is not None and not _has_valid_fileno(stream):
            kwargs[stream_name] = subprocess.PIPE


def _is_npx_command(cmd: Any) -> bool:
    """Check if the command is an npx invocation."""
    return isinstance(cmd, str) and os.path.basename(cmd).startswith(NPX_PREFIX)


def _wrap_npx_command(args: Tuple) -> Tuple:
    """Wrap npx commands with 'cmd /c' for Windows compatibility."""
    if not args or not isinstance(args[0], list) or not args[0]:
        return args
    
    if _is_npx_command(args[0][0]):
        original_cmd = args[0]
        wrapped_cmd = ['cmd', '/c'] + args[0]
        print("🔧 Wrapping npx command with cmd /c")
        print(f"   Before: {original_cmd}")
        print(f"   After:  {wrapped_cmd}")
        return (wrapped_cmd,) + args[1:]
    
    return args


class WindowsPatchedPopen(subprocess.Popen):
    """Popen subclass with Windows-specific fixes for MCP servers."""
    
    def __init__(self, *args, **kwargs):
        _replace_invalid_streams(kwargs)
        args = _wrap_npx_command(args)
        super().__init__(*args, **kwargs)


def winpatch_mcpserver_stdio() -> None:
    """
    Patch subprocess.Popen to enable MCPServerStdio on Windows.
    This shall only affect Jupyter notbook on Windows, that is using WindowsSelectorEventLoop
    
    Fixes two Windows compatibility issues:
    1. Replaces streams without fileno() support (e.g., Jupyter) with PIPE
    2. Wraps npx commands with 'cmd /c' for proper execution
    """
    print(f"Platform detected: {platform.system()}")
    if platform.system() != "Windows":
        return
    
    subprocess.Popen = WindowsPatchedPopen
    print("✅ Applied Windows fix for MCPServerStdio")
