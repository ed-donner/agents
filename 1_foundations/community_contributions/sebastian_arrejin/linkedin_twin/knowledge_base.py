import hashlib
import json
import math
import re
import unicodedata
from collections import Counter
import numpy as np
from openai import OpenAI, OpenAIError
from pypdf import PdfReader
from config import KNOWLEDGE_DIR, EMBEDDINGS_CACHE, EMBEDDING_MODEL

MAX_CHUNK_CHARS = 1200
SUPPORTED_SUFFIXES = {".md", ".txt", ".pdf"}


def read_document(path):
    if path.suffix.lower() == ".pdf":
        reader = PdfReader(path)
        return "\n".join(page.extract_text() or "" for page in reader.pages)
    return path.read_text(encoding="utf-8")


def split_into_chunks(text):
    chunks = []
    for section in re.split(r"(?m)^(?=#{1,3} )", text):
        section = section.strip()
        while len(section) > MAX_CHUNK_CHARS:
            cut = section.rfind("\n", 0, MAX_CHUNK_CHARS)
            if cut <= 0:
                cut = MAX_CHUNK_CHARS
            chunks.append(section[:cut].strip())
            section = section[cut:].strip()
        if section:
            chunks.append(section)
    return chunks


def load_chunks():
    chunks = []
    for path in sorted(KNOWLEDGE_DIR.iterdir()):
        if path.name.startswith("_") or path.suffix.lower() not in SUPPORTED_SUFFIXES:
            continue
        for text in split_into_chunks(read_document(path)):
            chunks.append({"source": path.name, "text": text})
    return chunks


def tokenize(text):
    text = unicodedata.normalize("NFKD", text.lower())
    text = "".join(char for char in text if not unicodedata.combining(char))
    return [word for word in re.findall(r"\w+", text) if len(word) > 1]


class KeywordIndex:
    """TF-IDF index, used when the configured endpoint cannot produce embeddings."""

    def __init__(self, texts):
        documents = [Counter(tokenize(text)) for text in texts]
        document_frequency = Counter(word for document in documents for word in document)
        self.idf = {word: math.log((len(documents) + 1) / (count + 1)) + 1 for word, count in document_frequency.items()}
        self.vectors = [self._weigh(document) for document in documents]

    def _weigh(self, counts):
        weights = {word: count * self.idf[word] for word, count in counts.items() if word in self.idf}
        norm = math.sqrt(sum(weight * weight for weight in weights.values())) or 1.0
        return {word: weight / norm for word, weight in weights.items()}

    def scores(self, query):
        query_vector = self._weigh(Counter(tokenize(query)))
        return np.array([sum(weight * vector.get(word, 0.0) for word, weight in query_vector.items()) for vector in self.vectors])


class KnowledgeBase:
    """Small in-memory RAG store: OpenAI embeddings + cosine similarity, with a TF-IDF fallback."""

    def __init__(self, client: OpenAI):
        self.client = client
        self.chunks = load_chunks()
        self.vectors = self._embed_chunks() if self.chunks else None
        self.keyword_index = KeywordIndex([chunk["text"] for chunk in self.chunks]) if self.vectors is None else None
        mode = "embeddings" if self.vectors is not None else "keyword (TF-IDF)"
        print(f"Knowledge base loaded: {len(self.chunks)} chunks, search mode: {mode}", flush=True)

    def _embed(self, texts):
        response = self.client.embeddings.create(model=EMBEDDING_MODEL, input=texts, encoding_format="float")
        vectors = [item.embedding for item in response.data]
        if len(vectors) != len(texts) or not all(vectors):
            raise ValueError("the embeddings endpoint returned empty vectors")
        return vectors

    def _embed_chunks(self):
        cache = {}
        if EMBEDDINGS_CACHE.exists():
            cache = json.loads(EMBEDDINGS_CACHE.read_text(encoding="utf-8"))
        if cache.get("model") != EMBEDDING_MODEL or cache.get("base_url") != str(self.client.base_url):
            cache = {"model": EMBEDDING_MODEL, "base_url": str(self.client.base_url), "vectors": {}}

        keys = [hashlib.sha256(chunk["text"].encode("utf-8")).hexdigest() for chunk in self.chunks]
        missing = {key: chunk["text"] for key, chunk in zip(keys, self.chunks) if key not in cache["vectors"]}
        if missing:
            try:
                vectors = self._embed(list(missing.values()))
            except (OpenAIError, ValueError) as error:
                print(f"Embeddings unavailable ({error}); falling back to keyword search", flush=True)
                return None
            cache["vectors"].update(zip(missing.keys(), vectors))
            cache["vectors"] = {key: cache["vectors"][key] for key in keys}
            EMBEDDINGS_CACHE.write_text(json.dumps(cache), encoding="utf-8")

        matrix = np.array([cache["vectors"][key] for key in keys])
        return matrix / np.linalg.norm(matrix, axis=1, keepdims=True)

    def search(self, query, k=4):
        if not self.chunks:
            return []
        if self.vectors is not None:
            query_vector = np.array(self._embed([query])[0])
            scores = self.vectors @ (query_vector / np.linalg.norm(query_vector))
        else:
            scores = self.keyword_index.scores(query)
        best = [i for i in np.argsort(scores)[::-1][:k] if scores[i] > 0]
        return [{**self.chunks[i], "score": round(float(scores[i]), 3)} for i in best]
