from __future__ import annotations

import hashlib
import importlib
import logging
import re
from datetime import datetime, timezone
from typing import Any

from asket_mcp.config import get_settings

logger = logging.getLogger(__name__)

_COLLECTION = "psb_semantic_memory"

_INSTALL_HELP = (
    "Install semantic extras: uv sync --extra semantic (requires chromadb and openai)."
)


def _require_openai_key() -> str:
    key = (get_settings().openai_api_key or "").strip()
    if not key:
        raise ValueError(
            "OPENAI_API_KEY is not set. Add it to your environment or .env for semantic memory."
        )
    return key


def chunk_text(text: str, max_chars: int | None = None, overlap: int | None = None) -> list[str]:
    settings = get_settings()
    max_c = max_chars if max_chars is not None else settings.semantic_chunk_chars
    ov = overlap if overlap is not None else settings.semantic_chunk_overlap
    raw = (text or "").strip()
    if not raw:
        return []
    if len(raw) <= max_c:
        return [raw]

    parts = re.split(r"\n\s*\n+", raw)
    chunks: list[str] = []
    buf = ""
    for p in parts:
        p = p.strip()
        if not p:
            continue
        if len(buf) + len(p) + 2 <= max_c:
            buf = f"{buf}\n\n{p}" if buf else p
        else:
            if buf:
                chunks.append(buf)
            if len(p) <= max_c:
                buf = p
            else:
                for i in range(0, len(p), max_c - ov):
                    chunks.append(p[i : i + max_c])
                buf = ""
    if buf:
        chunks.append(buf)
    return chunks


def _embedding_function() -> Any:
    _ensure_chroma_imports()
    from chromadb.utils.embedding_functions import OpenAIEmbeddingFunction

    s = get_settings()
    return OpenAIEmbeddingFunction(api_key=_require_openai_key(), model_name=s.embedding_model)


def _ensure_chroma_imports() -> None:
    try:
        importlib.import_module("chromadb")
    except ImportError as e:
        raise RuntimeError(_INSTALL_HELP) from e


def _client():
    _ensure_chroma_imports()
    import chromadb

    path = str(get_settings().chroma_dir())
    logger.debug("Chroma persist path: %s", path)
    return chromadb.PersistentClient(path=path)


def _collection():
    client = _client()
    return client.get_or_create_collection(
        name=_COLLECTION,
        embedding_function=_embedding_function(),
        metadata={"hnsw:space": "cosine"},
    )


def ingest_text_chunks(
    text: str,
    *,
    source_id: str,
    extra_metadata: dict[str, Any] | None = None,
) -> str:
    _require_openai_key()
    chunks = chunk_text(text)
    if not chunks:
        return "Nothing to ingest (empty text)."
    coll = _collection()
    try:
        coll.delete(where={"source_id": source_id})
    except Exception as ex:
        logger.debug("chroma delete before ingest (ok if none): %s", ex)

    now = datetime.now(timezone.utc).isoformat()
    base_meta = {"source_id": source_id, "ingested_at": now, **(extra_metadata or {})}
    ids: list[str] = []
    documents: list[str] = []
    metadatas: list[dict[str, Any]] = []
    for i, doc in enumerate(chunks):
        h = hashlib.sha256(f"{source_id}:{i}:{doc[:200]}".encode()).hexdigest()[:16]
        chunk_id = f"{source_id}::chunk{i}::{h}"
        ids.append(chunk_id)
        documents.append(doc)
        metadatas.append({**base_meta, "chunk_index": i})
    coll.add(ids=ids, documents=documents, metadatas=metadatas)
    return f"Ingested {len(chunks)} chunk(s) under source_id={source_id!r}."


def semantic_search(query: str, top_k: int | None = None) -> list[dict[str, Any]]:
    _require_openai_key()
    k = top_k if top_k is not None else get_settings().rag_top_k
    coll = _collection()
    res = coll.query(query_texts=[query.strip()], n_results=max(1, min(k, 48)))
    out: list[dict[str, Any]] = []
    ids = (res.get("ids") or [[]])[0]
    docs = (res.get("documents") or [[]])[0]
    dists = (res.get("distances") or [[]])[0]
    metas = (res.get("metadatas") or [[]])[0]
    for i in range(len(ids)):
        out.append(
            {
                "id": ids[i],
                "document": docs[i] if i < len(docs) else "",
                "distance": dists[i] if i < len(dists) else None,
                "metadata": metas[i] if i < len(metas) else {},
            }
        )
    return out


def format_search_results(results: list[dict[str, Any]], max_snippet: int = 1200) -> str:
    if not results:
        return "No matching passages in semantic memory."
    lines: list[str] = []
    for r in results:
        meta = r.get("metadata") or {}
        src = meta.get("source_id", "?")
        dist = r.get("distance")
        dist_s = f"{dist:.4f}" if isinstance(dist, (int, float)) else str(dist)
        body = (r.get("document") or "").strip()
        if len(body) > max_snippet:
            body = body[: max_snippet - 1] + "…"
        lines.append(f"[source={src} score~={dist_s}]\n{body}\n")
    return "\n---\n".join(lines)


def collection_count() -> int:
    _require_openai_key()
    coll = _collection()
    return int(coll.count())
