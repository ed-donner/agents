"""Load profile resources from local files or configured public file URLs."""

import os
import re
from pathlib import Path
from urllib.parse import parse_qs, urlencode, urlparse

import requests

DOCS_DIR = Path(__file__).resolve().parent / "docs"


def download_url(url):
    parsed = urlparse(url)
    if parsed.scheme != "https" or not parsed.netloc:
        raise ValueError("Document URLs must use HTTPS")
    if parsed.hostname == "drive.google.com":
        match = re.fullmatch(r"/file/d/([\w-]+)(?:/.*)?", parsed.path)
        query = parse_qs(parsed.query)
        file_id = match.group(1) if match else query.get("id", [None])[0]
        if not file_id:
            raise ValueError("Use an individual Google Drive file link, not a folder link")
        parameters = {"export": "download", "id": file_id}
        if query.get("resourcekey"):
            parameters["resourcekey"] = query["resourcekey"][0]
        return "https://drive.google.com/uc?" + urlencode(parameters)
    return url


def read_document(filename, env_var):
    """Configured URLs take precedence; otherwise read the local docs file."""
    url = os.getenv(env_var, "").strip()
    if url:
        response = requests.get(download_url(url), timeout=20)
        response.raise_for_status()
        content = response.content
        if ("text/html" in response.headers.get("Content-Type", "").lower()
                or content.lstrip().lower().startswith((b"<!doctype html", b"<html"))):
            raise ValueError(f"{env_var} returned HTML instead of a document; check public download access")
    else:
        content = (DOCS_DIR / filename).read_bytes()
    if filename.endswith(".pdf") and b"%PDF-" not in content[:1024]:
        raise ValueError(f"{filename} is not a PDF document")
    return content
