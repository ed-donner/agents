"""Load job description and resume from .txt / common encodings or .pdf."""

from __future__ import annotations

from pathlib import Path


def read_input_text(path: Path) -> str:
    """
    Read plain text or extract text from PDF.

    Text files: try UTF-8, UTF-8-BOM, Windows-1252, then Latin-1.
    """
    if not path.is_file():
        raise FileNotFoundError(path)

    suffix = path.suffix.lower()
    if suffix == ".pdf":
        return _read_pdf_text(path)

    raw = path.read_bytes()
    for encoding in ("utf-8", "utf-8-sig", "cp1252", "latin-1"):
        try:
            return raw.decode(encoding)
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", errors="replace")


def _read_pdf_text(path: Path) -> str:
    try:
        from pypdf import PdfReader
    except ImportError as err:
        raise SystemExit(
            "Reading .pdf requires pypdf. Run: python -m pip install pypdf\n"
            "Or use a .txt resume with --resume path/to/resume.txt"
        ) from err

    reader = PdfReader(path)
    parts: list[str] = []
    for page in reader.pages:
        extracted = page.extract_text()
        if extracted:
            parts.append(extracted)
    text = "\n".join(parts).strip()
    if not text:
        raise SystemExit(f"No text could be extracted from PDF: {path}")
    return text
