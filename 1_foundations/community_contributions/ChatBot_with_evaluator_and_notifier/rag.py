import os
import glob
from typing import Optional, List, Dict, Any
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma

DB_NAME = os.getenv("DB_NAME", "career_db")
DIRECTORY_NAME = os.getenv("DIRECTORY_NAME", "knowledge_base")
CHROMA_PERSIST_DIRECTORY = os.getenv("CHROMA_PERSIST_DIRECTORY", "./chroma_db")
TOP_K = int(os.getenv("TOP_K", "25"))
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "1000"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "300"))
MODEL_NAME = os.getenv("EMBED_MODEL", "sentence-transformers/all-MiniLM-L6-v2")

class Retriever:
    def __init__(
        self,
        db_name: str = DB_NAME,
        directory_name: str = DIRECTORY_NAME,
        top_k: int = TOP_K,
        chunk_size: int = CHUNK_SIZE,
        chunk_overlap: int = CHUNK_OVERLAP,
        model_name: str = MODEL_NAME,
        force_rebuild: bool = False,
    ):
        self.db_name = db_name
        self.directory_name = directory_name
        self.top_k = top_k
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self._embeddings = HuggingFaceEmbeddings(model_name=model_name)
        self.vectorstore = None
        self._retriever = None
        self._init_or_load_db(force_rebuild=force_rebuild)

    def _get_documents(self) -> List:
        text_loader_kwargs = {"encoding": "utf-8"}
        docs = []
        for pattern in ("*.txt", "*.md", "*.markdown"):
            loader = DirectoryLoader(
                self.directory_name,
                glob=pattern,
                loader_cls=TextLoader,
                loader_kwargs=text_loader_kwargs,
                show_progress=False,
            )
            docs.extend(loader.load())
        return docs

    def _build_store(self):
        documents = self._get_documents()
        if documents:
            splitter = RecursiveCharacterTextSplitter(
                chunk_size=self.chunk_size,
                chunk_overlap=self.chunk_overlap,
            )
            chunks = splitter.split_documents(documents)
            if chunks:
                self.vectorstore = Chroma.from_documents(
                    documents=chunks,
                    embedding=self._embeddings,
                    persist_directory=self.db_name,
                )
            else:
                self.vectorstore = Chroma(
                    persist_directory=self.db_name,
                    embedding_function=self._embeddings,
                )
        else:
            self.vectorstore = Chroma(
                persist_directory=self.db_name,
                embedding_function=self._embeddings,
            )
        # Persistence is handled automatically when using persist_directory

    def _init_or_load_db(self, force_rebuild: bool = False):
        exists = os.path.exists(self.db_name) and any(
            os.scandir(self.db_name)
        )
        if force_rebuild or not exists:
            self._build_store()
        else:
            self.vectorstore = Chroma(
                persist_directory=self.db_name,
                embedding_function=self._embeddings,
            )
        self._retriever = self.vectorstore.as_retriever(
            search_type="similarity_score_threshold",
            search_kwargs={"k": self.top_k, "score_threshold": 0.2},
        )

    def rebuild(self):
        self._build_store()
        self._retriever = self.vectorstore.as_retriever(
            search_type="similarity_score_threshold",
            search_kwargs={"k": self.top_k, "score_threshold": 0.2},
        )

    def get_retriever(self, k: Optional[int] = None):
        if k and k != self.top_k:
            return self.vectorstore.as_retriever(search_kwargs={"k": k})
        return self._retriever

    def get_relevant_docs(self, message: str, k: Optional[int] = None):
        if k:
            # respect threshold on ad-hoc calls
            retr = self.vectorstore.as_retriever(
                search_type="similarity_score_threshold",
                search_kwargs={"k": k, "score_threshold": 0.2},
            )
            return retr.invoke(message)
        return self._retriever.invoke(message)

    def get_relevant_chunks(self, message: str, k: Optional[int] = None):
        docs = self.get_relevant_docs(message, k=k)
        return [d.page_content for d in docs]


# --- Back-compat free functions expected by controller/app ---
_GLOBAL_RETRIEVER: Optional[Retriever] = None


def get_retriever()  -> Any:
    """
    Returns a LangChain retriever object with get_relevant_documents().
    Lazily initializes a module-level Retriever to persist across calls.
    """
    global _GLOBAL_RETRIEVER
    if _GLOBAL_RETRIEVER is None:
        _GLOBAL_RETRIEVER = Retriever()
    return _GLOBAL_RETRIEVER.get_retriever()


def ingest(data_dir: Optional[str] = None) -> str:
    """
    Rebuilds the vector store using documents from data_dir or default DIRECTORY_NAME.
    Returns a short status string for UI display.
    """
    target_dir = data_dir or DIRECTORY_NAME
    global _GLOBAL_RETRIEVER
    _GLOBAL_RETRIEVER = Retriever(directory_name=target_dir, force_rebuild=True)
    count = getattr(_GLOBAL_RETRIEVER.vectorstore._collection, "count", lambda: 0)()
    return f"ingested from {target_dir} — chunks in store: {count}"


class ChromaRAG:
    """Minimal agent-style RAG wrapper: ingest, retrieve, metadata."""

    def __init__(
        self,
        persist_dir: str = CHROMA_PERSIST_DIRECTORY,
        kb_dir: str = DIRECTORY_NAME,
        model_name: str = os.getenv("EMBED_MODEL", "sentence-transformers/all-MiniLM-L6-v2"),
    ):
        self.persist_dir = persist_dir
        self.kb_dir = kb_dir
        self._embeddings = HuggingFaceEmbeddings(model_name=model_name)
        self._vs = None
        self._ensure_vectorstore()

    def _ensure_vectorstore(self):
        if os.path.exists(self.persist_dir) and any(os.scandir(self.persist_dir)):
            self._vs = Chroma(persist_directory=self.persist_dir, embedding_function=self._embeddings)
            print(f"[rag] loaded vectorstore at {self.persist_dir}")
        else:
            os.makedirs(self.persist_dir, exist_ok=True)
            self._vs = Chroma(persist_directory=self.persist_dir, embedding_function=self._embeddings)
            print(f"[rag] initialized empty vectorstore at {self.persist_dir}")

    def ingest_documents(self, folder_path: Optional[str] = None) -> Dict[str, Any]:
        folder = folder_path or self.kb_dir
        text_loader_kwargs = {"encoding": "utf-8"}
        docs: List = []
        for pattern in ("*.txt", "*.md", "*.markdown"):
            loader = DirectoryLoader(folder, glob=pattern, loader_cls=TextLoader, loader_kwargs=text_loader_kwargs, show_progress=False)
            docs.extend(loader.load())

        if not docs:
            print(f"[rag] no documents in {folder}")
            return {"ingested": 0, "total": getattr(self._vs._collection, "count", lambda: 0)()}

        splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        chunks = splitter.split_documents(docs)
        if not chunks:
            print("[rag] no chunks produced")
            return {"ingested": 0, "total": getattr(self._vs._collection, "count", lambda: 0)()}

        Chroma.from_documents(documents=chunks, embedding=self._embeddings, persist_directory=self.persist_dir)
        self._ensure_vectorstore()
        total = getattr(self._vs._collection, "count", lambda: 0)()
        print(f"[rag] ingested={len(chunks)} total={total}")
        return {"ingested": len(chunks), "total": total}

    def retrieve_context(self, query: str, top_k: int = 3) -> List[str]:
        retriever = self._vs.as_retriever(search_kwargs={"k": top_k})
        docs = retriever.invoke(query)
        return [d.page_content for d in docs]

    def get_retrieval_metadata(self, query: str, top_k: int = 3) -> Dict[str, Any]:
        retriever = self._vs.as_retriever(search_kwargs={"k": top_k})
        docs = retriever.invoke(query)
        results: List[Dict[str, Any]] = []
        for d in docs:
            results.append({"content": d.page_content, "metadata": getattr(d, "metadata", {})})
        return {"query": query, "results": results}
