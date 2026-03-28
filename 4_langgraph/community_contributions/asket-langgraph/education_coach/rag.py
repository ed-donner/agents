from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Callable, Optional

from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from langchain_core.tools import tool
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

from education_coach.config import _project_root, get_settings

logger = logging.getLogger(__name__)

_vectorstore: Optional[FAISS] = None


def course_materials_dir() -> Path:
    s = get_settings()
    if s.course_materials_path:
        return Path(s.course_materials_path).expanduser().resolve()
    return _project_root() / "course_materials"


def load_course_documents(root: Path) -> list[Document]:
    if not root.is_dir():
        return []
    docs: list[Document] = []
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        if path.name.startswith("."):
            continue
        if path.suffix.lower() not in {".md", ".txt"}:
            continue
        if path.name.lower() in {"readme.md", "readme.txt"}:
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        rel = path.relative_to(root).as_posix()
        docs.append(Document(page_content=text, metadata={"source": rel}))
    return docs


def documents_to_chunks(documents: list[Document]) -> list[Document]:
    s = get_settings()
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=s.rag_chunk_size,
        chunk_overlap=s.rag_chunk_overlap,
    )
    chunks: list[Document] = []
    for doc in documents:
        pieces = splitter.split_text(doc.page_content)
        src = doc.metadata.get("source", "unknown")
        for i, piece in enumerate(pieces):
            if not piece.strip():
                continue
            sid = f"{src}#{i}"
            chunks.append(
                Document(
                    page_content=piece.strip(),
                    metadata={"source": src, "chunk_index": i, "source_id": sid},
                )
            )
    return chunks


def build_vectorstore_from_dir(
    root: Path,
    *,
    embeddings_factory: Callable[[], Any],
) -> Optional[FAISS]:
    documents = load_course_documents(root)
    if not documents:
        logger.info("Course RAG: no .md/.txt under %s", root)
        return None
    chunks = documents_to_chunks(documents)
    if not chunks:
        return None
    embeddings = embeddings_factory()
    vs = FAISS.from_documents(chunks, embeddings)
    logger.info("Course RAG: indexed %s chunks from %s files", len(chunks), len(documents))
    return vs


def course_materials_ready() -> bool:
    s = get_settings()
    if not s.rag_enabled:
        return False
    if not (s.openai_api_key or "").strip():
        return False
    return bool(load_course_documents(course_materials_dir()))


def ensure_course_vectorstore() -> Optional[FAISS]:
    global _vectorstore
    if not course_materials_ready():
        return None
    if _vectorstore is not None:
        return _vectorstore
    root = course_materials_dir()
    s = get_settings()
    _vectorstore = build_vectorstore_from_dir(
        root,
        embeddings_factory=lambda: OpenAIEmbeddings(model=s.openai_embedding_model),
    )
    return _vectorstore


def reset_course_vectorstore_cache() -> None:
    global _vectorstore
    _vectorstore = None


def course_search_results(query: str, vectorstore: FAISS) -> str:
    s = get_settings()
    k = max(1, s.rag_top_k)
    docs = vectorstore.similarity_search(query.strip(), k=k)
    blocks: list[str] = []
    for doc in docs:
        sid = doc.metadata.get("source_id") or doc.metadata.get("source", "?")
        blocks.append(f"[SOURCE: {sid}]\n{doc.page_content}")
    return "\n\n".join(blocks) if blocks else "(no matching excerpts)"


def build_course_search_tool_lazy():
    @tool
    def search_course_materials(query: str) -> str:
        """Search instructor-provided course readings and notes (markdown/text in course_materials/).

        Use for syllabus topics, definitions, policies, and readings specific to this course.
        When you use excerpts from this tool, cite the exact [SOURCE: ...] tag in your reply."""
        q = (query or "").strip()
        if not q:
            return "Provide a non-empty search query."
        vs = ensure_course_vectorstore()
        if vs is None:
            return "Course search is not available."
        return course_search_results(q, vs)

    return search_course_materials
