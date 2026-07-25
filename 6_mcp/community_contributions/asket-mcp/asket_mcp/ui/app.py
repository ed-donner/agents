from __future__ import annotations

import logging
import os
import sys
from pathlib import Path

logger = logging.getLogger(__name__)


def _merge_no_proxy_loopback() -> None:
    extra = ("127.0.0.1", "localhost", "::1")
    for key in ("NO_PROXY", "no_proxy"):
        cur = (os.environ.get(key) or "").strip()
        parts = [p.strip() for p in cur.split(",") if p.strip()] if cur else []
        for host in extra:
            if host not in parts:
                parts.append(host)
        os.environ[key] = ",".join(parts)


def _ensure_streamlit_usable() -> None:
    try:
        import importlib.util

        if importlib.util.find_spec("streamlit") is None:
            raise ImportError
    except ImportError:
        print(
            "asket-mcp-ui needs Streamlit.\n\n"
            "Fix (from the `asket-mcp` directory):\n"
            "  uv sync --extra ui --extra semantic\n\n"
            "If imports still fail:\n"
            "  rm -rf .venv && uv sync --extra ui --extra semantic\n",
            file=sys.stderr,
        )
        sys.exit(2)


def main() -> None:
    from dotenv import load_dotenv

    _ensure_streamlit_usable()
    load_dotenv()
    from asket_mcp.logging_config import configure_logging

    configure_logging()
    from asket_mcp.config import get_settings

    settings = get_settings()
    _merge_no_proxy_loopback()

    host = os.getenv("ASKET_UI_HOST", "127.0.0.1")
    port = str(int(os.getenv("ASKET_UI_PORT", "7860")))

    if host in ("0.0.0.0", "::"):
        logger.warning(
            "Streamlit listens on all interfaces (%s). Use a reverse proxy + auth when exposing beyond LAN.",
            host,
        )

    ssl_cert = settings.ui_ssl_certfile
    ssl_key = settings.ui_ssl_keyfile
    if bool(ssl_cert) ^ bool(ssl_key):
        logger.error(
            "Set both ASKET_UI_SSL_CERTFILE and ASKET_UI_SSL_KEYFILE for HTTPS, or neither."
        )
        sys.exit(1)
    if ssl_cert and ssl_key:
        logger.warning(
            "Streamlit TLS is not wired through this launcher; terminate TLS at a reverse proxy "
            "(Caddy/nginx) or run `streamlit run` with your own SSL config."
        )

    app_path = Path(__file__).resolve().parent / "streamlit_app.py"
    os.environ.setdefault("STREAMLIT_BROWSER_GATHER_USAGE_STATS", "false")

    argv = [
        sys.executable,
        "-m",
        "streamlit",
        "run",
        str(app_path),
        f"--server.port={port}",
        f"--server.address={host}",
        "--server.headless=true",
        "--browser.gatherUsageStats=false",
    ]
    root = (settings.ui_root_path or "").strip()
    if root:
        argv.append(f"--server.baseUrlPath={root.strip('/')}")

    logger.info("Starting Streamlit: %s", " ".join(argv[4:]))
    os.execv(sys.executable, argv)


if __name__ == "__main__":
    main()
