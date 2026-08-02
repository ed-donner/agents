"""Job agency helpers: browser tools, file output, Pushover notifications."""

import json
import os
from datetime import datetime, timezone
from pathlib import Path

import requests
from dotenv import load_dotenv
from langchain_community.agent_toolkits import PlayWrightBrowserToolkit
from playwright.async_api import async_playwright

load_dotenv(override=True)

OUTPUT_DIR = Path(__file__).resolve().parent / "output"
PUSHOVER_URL = "https://api.pushover.net/1/messages.json"

async def playwright_tools():
    """Return Playwright browser tools plus lifecycle handles."""
    playwright = await async_playwright().start()
    browser = await playwright.chromium.launch(headless=False)
    toolkit = PlayWrightBrowserToolkit.from_browser(async_browser=browser)
    return toolkit.get_tools(), browser, playwright


def ensure_output_dir() -> Path:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    return OUTPUT_DIR


def save_job_results(markdown: str, payload: dict) -> tuple[Path, Path]:
    """Write markdown + JSON next to this package."""
    ensure_output_dir()
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    base = OUTPUT_DIR / f"job_search_{stamp}"
    md_path = base.with_suffix(".md")
    json_path = base.with_suffix(".json")
    md_path.write_text(markdown, encoding="utf-8")
    json_path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    return md_path, json_path


def notify_user(message: str) -> str:
    """Send Pushover notification if credentials are set; otherwise no-op."""
    token = os.getenv("PUSHOVER_TOKEN")
    user = os.getenv("PUSHOVER_USER")
    if not token or not user:
        return "skipped_no_pushover_credentials"
    try:
        requests.post(
            PUSHOVER_URL,
            data={"token": token, "user": user, "message": message},
            timeout=30,
        ).raise_for_status()
    except Exception as exc:  # noqa: BLE001
        return f"pushover_failed:{exc!s}"
    return "sent"
