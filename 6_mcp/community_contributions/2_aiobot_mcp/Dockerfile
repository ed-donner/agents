# Use Python 3.11 (not 3.12+)
FROM python:3.11-slim

# Install uv, Node.js and npm for MCP server
RUN pip install --no-cache-dir uv && \
    apt-get update && \
    apt-get install -y nodejs npm && \
    rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy dependency files first (changes rarely)
COPY pyproject.toml uv.lock ./

# Put venv outside of /app so it won't be affected by volume mounts
ENV UV_PROJECT_ENVIRONMENT=/opt/venv

# Install dependencies (this will now create venv at /opt/venv)
RUN uv sync --locked

# Copy all source code
COPY . .

# Set environment variables
ENV PYTHONPATH=/app/src
ENV PYTHONUNBUFFERED=1
ENV DOCKER_ENV=1

# Disable UV cache entirely for production
ENV UV_NO_CACHE=1

# Expose the port
EXPOSE 7860

# Run the application
CMD ["uv", "run", "app.py"]
