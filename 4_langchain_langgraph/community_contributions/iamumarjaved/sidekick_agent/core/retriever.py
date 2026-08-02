from __future__ import annotations
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional


try:
    import chromadb
    from chromadb.config import Settings
    CHROMADB_AVAILABLE = True
except ImportError:
    chromadb = None
    Settings = None
    CHROMADB_AVAILABLE = False
try:
    from sentence_transformers import CrossEncoder, SentenceTransformer
    CROSS_ENCODER_AVAILABLE = True
except ImportError:
    CrossEncoder = None
    SentenceTransformer = None
    CROSS_ENCODER_AVAILABLE = False


class GuidelineRetriever:
    """Advanced RAG retriever backed by ChromaDB with semantic-first chunking."""

    def __init__(
        self,
        sources: Dict[str, str],
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        collection_name: str = "guidelines",
    ) -> None:
        self.sources = sources
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.collection_name = collection_name

        self.embeddings_model: Optional[SentenceTransformer] = None
        self.cross_encoder: Optional[CrossEncoder] = None
        self.collection_prepared = False
        self.client = None
        self.collection = None

        self._initialise_embeddings()
        self._initialise_cross_encoder()
        self._initialise_chromadb()


    def _initialise_embeddings(self) -> None:
        try:
            if SentenceTransformer is None:
                raise RuntimeError("sentence-transformers not installed")
            os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
            self.embeddings_model = SentenceTransformer("all-MiniLM-L6-v2", device="cpu")
            print("Embedding model loaded successfully!")
        except Exception as exc:
            self.embeddings_model = None
            print(f"WARNING: Failed to load sentence-transformers model: {exc}")
            print("Install with: pip install sentence-transformers")

    def _initialise_cross_encoder(self) -> None:
        if not CROSS_ENCODER_AVAILABLE or CrossEncoder is None:
            print("WARNING: CrossEncoder not available. Using single-stage retrieval.")
            return
        try:
            self.cross_encoder = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")
        except Exception as exc:
            self.cross_encoder = None
            print(f"WARNING: Failed to load cross-encoder: {exc}")

    def _initialise_chromadb(self) -> None:
        if not CHROMADB_AVAILABLE or chromadb is None or Settings is None:
            print("WARNING: ChromaDB not available. Install with: pip install chromadb")
            return

        try:
            db_path = Path(os.getenv("SIDEKICK_CHROMA_DB", Path.cwd() / "data" / "chroma_db"))
            db_path.mkdir(parents=True, exist_ok=True)
            print("Connecting to ChromaDB...")
            self.client = chromadb.PersistentClient(path=str(db_path), settings=Settings(anonymized_telemetry=False))
            print("ChromaDB client connected")
        except Exception as exc:
            self.client = None
            print(f"WARNING: ChromaDB initialization failed: {exc}. Falling back to basic retrieval.")


    def query(self, query: str, k: int = 10, rerank_k: int = 6) -> List[str]:
        if self.client and not self.collection_prepared:
            try:
                self._prepare_collection(self.sources)
                self.collection_prepared = True
                print("Collection prepared")
            except Exception as exc:
                print(f"WARNING: Failed to prepare collection: {exc}")
                self.collection = None

        if not self.collection:
            return []

        try:
            query_embedding = self._get_embedding(query)
            results = self.collection.query(query_embeddings=[query_embedding], n_results=min(k * 2, 20))
            documents = results.get("documents", [[]])
            if not documents or not documents[0]:
                return []

            candidates = documents[0]
            metadatas = results.get("metadatas", [[]])[0] if results.get("metadatas") else []

            if self.cross_encoder and len(candidates) > rerank_k:
                pairs = [[query, doc] for doc in candidates]
                scores = self.cross_encoder.predict(pairs)
                ranked = sorted(zip(candidates, scores, metadatas), key=lambda item: item[1], reverse=True)
                return [doc for doc, _, __ in ranked[:rerank_k]]

            return candidates[:rerank_k]
        except Exception as exc:
            print(f"Error in retrieval: {exc}")
            return []

    def full_corpus(self) -> str:
        if not self.collection:
            return ""
        try:
            results = self.collection.get()
            if results and results.get("documents"):
                return "\n\n".join(results["documents"])
        except Exception:
            return ""
        return ""


    def _get_embedding(self, text: str) -> List[float]:
        if self.embeddings_model:
            return self.embeddings_model.encode(text, convert_to_numpy=False).tolist()
        return [0.0] * 384

    def _prepare_collection(self, sources: Dict[str, str]) -> None:
        if not self.client:
            return
        if not self.embeddings_model:
            print("Warning: No embedding model available. Cannot create vector index.")
            self.collection = None
            return

        try:
            try:
                self.client.delete_collection(name=self.collection_name)
            except Exception:
                pass

            self.collection = self.client.create_collection(name=self.collection_name, metadata={"hnsw:space": "cosine"})
        except Exception as exc:
            print(f"Error creating ChromaDB collection: {exc}")
            self.collection = None
            return

        if not self.collection:
            return

        chunks, embeddings, metadatas, ids = [], [], [], []
        print(f"Processing {len(sources)} sources for indexing...")
        chunk_idx = 0

        for source_name, content in sources.items():
            if not content or not content.strip():
                print(f"Warning: Source '{source_name}' is empty, skipping.")
                continue
            try:
                segmented = self._semantic_chunk(content, source_name)
                print(f"  - {source_name}: {len(segmented)} chunks")
                for chunk in segmented:
                    chunk_id = f"{source_name}_{chunk_idx}"
                    ids.append(chunk_id)
                    chunks.append(chunk["text"])
                    metadatas.append({"source": source_name, "chunk_index": chunk_idx, "size": chunk["size"]})
                    embeddings.append(self._get_embedding(chunk["text"]))
                    chunk_idx += 1
            except Exception as exc:
                print(f"Error processing source '{source_name}': {exc}")

        if chunks:
            print(f"Adding {len(chunks)} chunks to ChromaDB...")
            self.collection.add(ids=ids, documents=chunks, embeddings=embeddings, metadatas=metadatas)
            print(f"Successfully indexed {len(chunks)} semantic chunks from {len(sources)} sources in ChromaDB")

    def _semantic_chunk(self, text: str, source_name: str) -> List[Dict[str, Any]]:
        chunks: List[Dict[str, Any]] = []
        paragraphs = re.split(r"\n\s*\n", text)
        current_chunk, current_size = "", 0

        for paragraph in paragraphs:
            paragraph = paragraph.strip()
            if not paragraph:
                continue

            paragraph_size = len(paragraph)
            if current_size + paragraph_size > self.chunk_size and current_chunk:
                chunks.append({"text": current_chunk.strip(), "source": source_name, "size": current_size})
                overlap = current_chunk[-self.chunk_overlap :] if len(current_chunk) > self.chunk_overlap else current_chunk
                current_chunk = f"{overlap}\n\n{paragraph}"
                current_size = len(current_chunk)
            else:
                current_chunk = f"{current_chunk}\n\n{paragraph}" if current_chunk else paragraph
                current_size = len(current_chunk)

        if current_chunk:
            chunks.append({"text": current_chunk.strip(), "source": source_name, "size": current_size})

        if not chunks and text.strip():
            chunks.append({"text": text.strip(), "source": source_name, "size": len(text)})

        return chunks

