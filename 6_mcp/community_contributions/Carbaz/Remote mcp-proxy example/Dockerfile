FROM python:3.13-slim

# Install uv (includes uvx)
RUN pip install uv

# Default command
CMD ["uvx", "mcp-proxy", "--port=8000", "--host=0.0.0.0", "uvx", "mcp-server-fetch"]
