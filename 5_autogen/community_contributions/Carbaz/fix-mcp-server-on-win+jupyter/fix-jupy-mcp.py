"""Windows + Jupyter fix for MCP server creation."""

# Jupyter on Windows has an issue with MCP stdio client due to how Jupyter captures
# "stderr".
#   See: https://github.com/modelcontextprotocol/python-sdk/issues/1103

# The MCP client internally uses "stdio_client()" to create a server process and Jupyter
# replaces "stderr" with a Python object (ipykernel.iostream.OutStream) that can't
# provide a real OS file descriptor, so "subprocess.Popen()" crashes when trying to use
# it.

# When "stderr=None" is passed instead of Jupyter's captured "stderr", the subprocess
# can start correctly.
#   Fix: https://github.com/modelcontextprotocol/python-sdk/issues/1103#issuecomment-3470416291

# We are not directly calling the "stdio_client" so we need to "monkey patch" it
# to pass "None" for "stderr" always.

import mcp


mcp.client.stdio._original_stdio_client = mcp.client.stdio.stdio_client
_errlog = open("mcp_stderr.log", "w", buffering=1)
patched = lambda server, *_: mcp.client.stdio._original_stdio_client(server, _errlog)  # noqa: E731
mcp.stdio_client = mcp.client.stdio.stdio_client = patched
