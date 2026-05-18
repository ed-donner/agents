"""
Bio Agent — RAG Pipeline
-------------------------
ChromaDB-backed knowledge retrieval.
Handles: PDF/text ingestion, chunking, and semantic search.
"""

import os
import chromadb
from pypdf import PdfReader

from config import CHROMA_PATH, KNOWLEDGE_DIR, RAG_COLLECTION_NAME, RAG_CHUNK_SIZE, RAG_CHUNK_OVERLAP, RAG_TOP_K


# ── Module State ───────────────────────────────────────────────────────

_collection = None  # lazily initialised


def _get_collection():
    """Return the ChromaDB collection, creating it if needed."""
    global _collection
    if _collection is None:
        client = chromadb.PersistentClient(path=CHROMA_PATH)
        _collection = client.get_or_create_collection(RAG_COLLECTION_NAME)
    return _collection


# ── Text Extraction ───────────────────────────────────────────────────

def _extract_pdf_text(path: str) -> str:
    """Extract all text from a PDF file."""
    reader = PdfReader(path)
    pages = []
    for page in reader.pages:
        text = page.extract_text()
        if text:
            pages.append(text.strip())
    return "\n\n".join(pages)


def _extract_txt(path: str) -> str:
    """Read a plain text file."""
    with open(path, "r", encoding="utf-8") as f:
        return f.read().strip()


# ── Chunking ──────────────────────────────────────────────────────────

def _chunk_text(text: str, chunk_size: int = RAG_CHUNK_SIZE, overlap: int = RAG_CHUNK_OVERLAP) -> list[str]:
    """
    Split text into roughly equal chunks by word count with overlap.
    Returns a list of text chunks.
    """
    words = text.split()
    chunks = []
    start = 0

    while start < len(words):
        end = start + chunk_size
        chunk = " ".join(words[start:end])
        if chunk:
            chunks.append(chunk)
        start += chunk_size - overlap  # step forward with overlap

    return chunks


# ── Ingestion ─────────────────────────────────────────────────────────

def ingest_knowledge() -> int:
    """
    Read all files from the knowledge directory, chunk them,
    and store in ChromaDB. Returns the number of chunks stored.

    Safe to call multiple times — skips if chunks already exist.
    """
    collection = _get_collection()

    # Skip if already ingested
    if collection.count() > 0:
        return collection.count()

    all_text_parts = []

    for filename in sorted(os.listdir(KNOWLEDGE_DIR)):
        filepath = os.path.join(KNOWLEDGE_DIR, filename)

        if filename.lower().endswith(".pdf"):
            all_text_parts.append(_extract_pdf_text(filepath))
        elif filename.lower().endswith(".txt"):
            all_text_parts.append(_extract_txt(filepath))

    if not all_text_parts:
        return 0

    combined = "\n\n".join(all_text_parts)
    chunks = _chunk_text(combined)

    if not chunks:
        return 0

    # Generate stable IDs based on position
    ids = [f"chunk_{i:04d}" for i in range(len(chunks))]

    collection.add(documents=chunks, ids=ids)

    return len(chunks)


# ── Search ────────────────────────────────────────────────────────────

def search_knowledge_base(query: str) -> str:
    """
    Retrieve the top-K most relevant chunks for a query.
    Returns a formatted string of the matching chunks.
    """
    collection = _get_collection()

    if collection.count() == 0:
        return "No knowledge base documents found. Please ingest knowledge first."

    results = collection.query(query_texts=[query], n_results=RAG_TOP_K)

    documents = results.get("documents", [[]])[0]

    if not documents:
        return "No relevant information found in the knowledge base."

    formatted = []
    for i, doc in enumerate(documents, 1):
        formatted.append(f"[Source {i}]\n{doc}")

    return "\n\n---\n\n".join(formatted)
