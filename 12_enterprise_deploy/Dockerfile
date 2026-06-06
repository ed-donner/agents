# Multi-stage production Docker build for the enterprise agent.
# Stage 1: build dependencies
# Stage 2: minimal runtime image

FROM python:3.12-slim AS builder

WORKDIR /build
COPY requirements.txt .
RUN pip install --no-cache-dir --target=/build/packages -r requirements.txt


FROM python:3.12-slim AS runtime

# Security: run as non-root user
RUN useradd -m -u 1000 agent
WORKDIR /app
USER agent

# Copy installed packages from builder
COPY --from=builder /build/packages /usr/local/lib/python3.12/site-packages

# Copy application code
COPY --chown=agent:agent agent_server.py middleware.py circuit_breaker.py ./

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"

EXPOSE 8000

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

CMD ["python", "-m", "uvicorn", "agent_server:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
