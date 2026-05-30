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

# Since stdio_client() is called internally by mcp_server_tools() and we can't pass
# parameters to it directly, we monkey patch stdio.stdio_client to always pass
# stderr=errors_file before the MCP session is created.

# With None, the subprocess will bypasses Jupyter's captured stream entirely but error
# logs will be lost, so we pass an already opened file so we can track it to see outputs.

import mcp


mcp.client.stdio._original_stdio_client = mcp.client.stdio.stdio_client
_errlog = open("mcp_stderr.log", "w", buffering=1)
patched = lambda server, *_: mcp.client.stdio._original_stdio_client(server, _errlog)  # noqa: E731
mcp.stdio_client = mcp.client.stdio.stdio_client = patched
