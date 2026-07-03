"""Chroma-backed RAG over Nairobi venue and rainy-season guidance (LangChain + OpenAI embeddings)."""

from functools import lru_cache

from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

from config import CHROMA_DIR, EMBEDDING_MODEL, VENUES_DOC


def _load_source_documents() -> list[Document]:
    text = VENUES_DOC.read_text(encoding="utf-8")
    splitter = RecursiveCharacterTextSplitter(chunk_size=600, chunk_overlap=80)
    return [Document(page_content=chunk) for chunk in splitter.split_text(text)]


@lru_cache(maxsize=1)
def _vectorstore() -> Chroma:
    CHROMA_DIR.mkdir(parents=True, exist_ok=True)
    embeddings = OpenAIEmbeddings(model=EMBEDDING_MODEL)
    if not any(CHROMA_DIR.iterdir()):
        docs = _load_source_documents()
        return Chroma.from_documents(
            documents=docs,
            embedding=embeddings,
            persist_directory=str(CHROMA_DIR),
            collection_name="nairobi_venues",
        )
    return Chroma(
        persist_directory=str(CHROMA_DIR),
        embedding_function=embeddings,
        collection_name="nairobi_venues",
    )


def retrieve_venues_context(query: str, k: int = 4) -> str:
    """Return top-k venue / safety snippets for the analysis agent."""
    try:
        vs = _vectorstore()
        docs = vs.similarity_search(query or "Nairobi restaurants rain flood safety", k=k)
    except Exception as exc: 
        return f"RAG retrieval failed (check OPENAI_API_KEY and chromadb): {exc}"

    if not docs:
        return "No venue documents retrieved."
    parts = ["Retrieved venue and safety context:\n"]
    for i, d in enumerate(docs, 1):
        parts.append(f"{i}. {d.page_content.strip()}\n")
    return "\n".join(parts)
