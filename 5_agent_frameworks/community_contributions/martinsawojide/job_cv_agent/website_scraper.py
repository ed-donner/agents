"""
website_scraper.py — JS-capable website scraper using undetected Chrome.

Uses undetected-chromedriver to bypass bot-detection on JavaScript-heavy sites,
then extracts the visible text from the fully rendered page.

Dependencies (install via uv from the project root):
    uv add undetected-chromedriver selenium

Usage:
    python website_scraper.py https://example.com
    python website_scraper.py https://openai.com https://anthropic.com
"""

import sys
import subprocess
import time

REQUIRED_PACKAGES = {
    "undetected_chromedriver": "undetected-chromedriver",
    "selenium": "selenium",
}


def _ensure_dependencies():
    """Check that all required packages are importable; install any that are missing via uv."""
    missing = []
    for module, package in REQUIRED_PACKAGES.items():
        try:
            __import__(module)
        except ImportError:
            missing.append(package)

    if missing:
        print(f"Missing packages: {', '.join(missing)}. Installing with uv...")
        subprocess.check_call(["uv", "add"] + missing)
        print("All dependencies installed.")


_ensure_dependencies()

import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


def fetch_js_website(url: str, *, headless: bool = True, timeout: int = 30) -> str:
    """
    Scrape the visible text of a JavaScript-rendered webpage.

    Launches a headless Chrome instance via undetected-chromedriver so that
    sites protected by Cloudflare, Akamai, or similar bot-detection don't
    block the request.  The browser fully renders the page (including JS),
    waits for the <body> element, and returns its inner text.

    Args:
        url:      The webpage URL to scrape.
        headless: Run Chrome without a visible window (default True).
        timeout:  Max seconds to wait for the page to load.

    Returns:
        The visible text content of the page body.
    """
    print(f"Scraper: launching browser for {url}")

    options = uc.ChromeOptions()
    options.page_load_strategy = "eager"
    if headless:
        options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-extensions")
    options.add_argument(
        "--user-agent=Mozilla/5.0 (X11; Linux x86_64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/131.0.0.0 Safari/537.36"
    )

    driver = uc.Chrome(options=options, use_subprocess=False, version_main=144)
    driver.set_page_load_timeout(timeout)

    try:
        print(f"Scraper: navigating to {url}")
        start = time.perf_counter()
        try:
            driver.get(url)
        except Exception:
            # Timeout on page load is expected for heavy sites; the body
            # may still be available thanks to the 'eager' load strategy.
            pass
        elapsed = time.perf_counter() - start
        print(f"Scraper: page response received ({elapsed:.1f}s), waiting for DOM...")

        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        # SPA sites hydrate after body appears — wait until text is non-empty
        WebDriverWait(driver, 20).until(
            lambda d: len(d.find_element(By.TAG_NAME, "body").text.strip()) > 100
        )

        content = driver.find_element(By.TAG_NAME, "body").text
    finally:
        driver.quit()

    word_count = len(content.split())
    print(f"Scraper: done — {word_count} words scraped from {url}")

    return content


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python website_scraper.py <url> [url ...]")
        sys.exit(1)

    for url in sys.argv[1:]:
        print(f"\nScraping: {url}")
        text = fetch_js_website(url)
        print(f"\n{text[:500]}{'...' if len(text) > 500 else ''}\n")
