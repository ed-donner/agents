FROM python:3.12-slim-bookworm

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends tzdata \
    && rm -rf /var/lib/apt/lists/*

ENV PYTHONUNBUFFERED=1 \
    ASKET_MCP_DATA_DIR=/data \
    ASKET_MCP_TRANSPORT=sse \
    ASKET_MCP_HOST=0.0.0.0 \
    ASKET_MCP_PORT=8765 \
    ASKET_UI_QUIET=true

COPY pyproject.toml README.md ./
COPY asket_mcp ./asket_mcp
ARG ASKET_INSTALL_EXTRAS="[ui,semantic]"
RUN pip install --no-cache-dir ".${ASKET_INSTALL_EXTRAS}" \
    && rm -rf /root/.cache/pip

RUN groupadd -r -g 10001 asket \
    && useradd -r -u 10001 -g asket -d /home/asket -m asket \
    && chown -R asket:asket /app

USER asket
WORKDIR /app

RUN mkdir -p /home/asket/.cache

VOLUME ["/data"]
EXPOSE 8765
EXPOSE 7860

HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
  CMD python -c "import os,socket; s=socket.socket(); s.settimeout(4); p=int(os.environ.get('ASKET_MCP_PORT','8765')); s.connect(('127.0.0.1',p)); s.close()"

CMD ["python", "-m", "asket_mcp.servers.app"]
