import os
import json
import pickle
from typing import List, Dict, Tuple, Optional
from pathlib import Path
import numpy as np
from sentence_transformers import SentenceTransformer, CrossEncoder
from rank_bm25 import BM25Okapi
import chromadb


class QueryExpander:
    
    def __init__(self, openai_client):
        self.client = openai_client
    
    def expand_query(self, query: str, num_variations: int = 3) -> List[str]:
        prompt = f"""Given this user query, generate {num_variations} alternative phrasings that capture the same intent but use different words.

Original query: {query}

Return ONLY a JSON array of alternative queries, nothing else.
Example: ["query1", "query2", "query3"]"""
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7
            )
            variations = json.loads(response.choices[0].message.content)
            return [query] + variations
        except Exception as e:
            print(f"Query expansion failed: {e}")
            return [query]


class HybridRetriever:
    
    def __init__(self, embedding_model: str = "all-MiniLM-L6-v2", reranker_model: str = "cross-encoder/ms-marco-MiniLM-L-6-v2", data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        
        print("Loading embedding model...")
        self.embedder = SentenceTransformer(embedding_model)
        
        print("Loading reranker model...")
        self.reranker = CrossEncoder(reranker_model)
        
        self.chroma_client = chromadb.PersistentClient(path=str(self.data_dir / "vector_store"))
        self.documents: List[Dict] = []
        self.bm25: Optional[BM25Okapi] = None
        self.collection = None
        
    def chunk_text(self, text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
        words = text.split()
        chunks = []
        for i in range(0, len(words), chunk_size - overlap):
            chunk = ' '.join(words[i:i + chunk_size])
            if chunk:
                chunks.append(chunk)
        return chunks
    
    def index_documents(self, documents: Dict[str, str], chunk_size: int = 500, overlap: int = 50, collection_name: str = "knowledge_base"):
        print(f"Indexing documents with chunk_size={chunk_size}, overlap={overlap}")
        
        all_chunks = []
        for doc_id, content in documents.items():
            chunks = self.chunk_text(content, chunk_size, overlap)
            for idx, chunk in enumerate(chunks):
                all_chunks.append({
                    "id": f"{doc_id}_{idx}",
                    "text": chunk,
                    "source": doc_id,
                    "chunk_idx": idx
                })
        
        self.documents = all_chunks
        
        if not all_chunks:
            raise ValueError("No text chunks created from documents. Please check your document content.")
        
        print("Building BM25 index...")
        tokenized_docs = [doc["text"].lower().split() for doc in all_chunks]
        self.bm25 = BM25Okapi(tokenized_docs)
        
        print("Building semantic index...")
        try:
            self.chroma_client.delete_collection(collection_name)
        except:
            pass
        
        self.collection = self.chroma_client.create_collection(name=collection_name, metadata={"hnsw:space": "cosine"})
        
        batch_size = 100
        for i in range(0, len(all_chunks), batch_size):
            batch = all_chunks[i:i + batch_size]
            self.collection.add(
                documents=[doc["text"] for doc in batch],
                ids=[doc["id"] for doc in batch],
                metadatas=[{"source": doc["source"], "chunk_idx": doc["chunk_idx"]} for doc in batch]
            )
        
        print(f"Indexed {len(all_chunks)} chunks from {len(documents)} documents")
        
        with open(self.data_dir / "bm25_index.pkl", "wb") as f:
            pickle.dump((self.bm25, self.documents), f)
    
    def retrieve_bm25(self, query: str, top_k: int = 10) -> List[Tuple[Dict, float]]:
        if self.bm25 is None:
            return []
        
        tokenized_query = query.lower().split()
        scores = self.bm25.get_scores(tokenized_query)
        top_indices = np.argsort(scores)[::-1][:top_k]
        
        results = []
        for idx in top_indices:
            if scores[idx] > 0:
                results.append((self.documents[idx], float(scores[idx])))
        return results
    
    def retrieve_semantic(self, query: str, top_k: int = 10) -> List[Tuple[Dict, float]]:
        if self.collection is None:
            return []
        
        results = self.collection.query(query_texts=[query], n_results=top_k)
        
        retrieved = []
        for i, doc_id in enumerate(results["ids"][0]):
            doc = next((d for d in self.documents if d["id"] == doc_id), None)
            if doc:
                distance = results["distances"][0][i]
                similarity = 1 / (1 + distance)
                retrieved.append((doc, similarity))
        return retrieved
    
    def retrieve_hybrid(self, query: str, top_k: int = 10, bm25_weight: float = 0.5, semantic_weight: float = 0.5) -> List[Tuple[Dict, float]]:
        bm25_results = self.retrieve_bm25(query, top_k * 2)
        semantic_results = self.retrieve_semantic(query, top_k * 2)
        
        def normalize_scores(results):
            if not results:
                return {}
            scores = [score for _, score in results]
            max_score = max(scores) if scores else 1.0
            min_score = min(scores) if scores else 0.0
            range_score = max_score - min_score if max_score != min_score else 1.0
            return {doc["id"]: (score - min_score) / range_score for doc, score in results}
        
        bm25_scores = normalize_scores(bm25_results)
        semantic_scores = normalize_scores(semantic_results)
        
        all_doc_ids = set(bm25_scores.keys()) | set(semantic_scores.keys())
        combined_scores = {}
        for doc_id in all_doc_ids:
            bm25_score = bm25_scores.get(doc_id, 0.0)
            semantic_score = semantic_scores.get(doc_id, 0.0)
            combined_scores[doc_id] = bm25_weight * bm25_score + semantic_weight * semantic_score
        
        sorted_ids = sorted(combined_scores.items(), key=lambda x: x[1], reverse=True)[:top_k]
        
        results = []
        for doc_id, score in sorted_ids:
            doc = next((d for d in self.documents if d["id"] == doc_id), None)
            if doc:
                results.append((doc, score))
        return results
    
    def rerank(self, query: str, documents: List[Tuple[Dict, float]], top_k: int = 5) -> List[Tuple[Dict, float]]:
        if not documents:
            return []
        
        pairs = [[query, doc["text"]] for doc, _ in documents]
        rerank_scores = self.reranker.predict(pairs)
        reranked = [(doc, float(score)) for (doc, _), score in zip(documents, rerank_scores)]
        reranked.sort(key=lambda x: x[1], reverse=True)
        return reranked[:top_k]
    
    def retrieve(self, query: str, method: str = "hybrid_rerank", top_k: int = 5, expand_query: bool = False, query_expander: Optional['QueryExpander'] = None, **kwargs) -> List[Dict]:
        queries = [query]
        
        if expand_query and query_expander:
            queries = query_expander.expand_query(query)
            print(f"Expanded to {len(queries)} queries")
        
        all_results = {}
        for q in queries:
            if method == "bm25":
                results = self.retrieve_bm25(q, top_k * 2)
            elif method == "semantic":
                results = self.retrieve_semantic(q, top_k * 2)
            elif method in ["hybrid", "hybrid_rerank"]:
                results = self.retrieve_hybrid(q, top_k * 2, kwargs.get("bm25_weight", 0.5), kwargs.get("semantic_weight", 0.5))
            else:
                raise ValueError(f"Unknown method: {method}")
            
            for doc, score in results:
                doc_id = doc["id"]
                if doc_id not in all_results:
                    all_results[doc_id] = (doc, 0.0)
                all_results[doc_id] = (doc, all_results[doc_id][1] + score)
        
        aggregated = list(all_results.values())
        aggregated.sort(key=lambda x: x[1], reverse=True)
        
        if "rerank" in method:
            print(f"Reranking {len(aggregated)} results...")
            aggregated = self.rerank(query, aggregated[:top_k * 3], top_k)
        else:
            aggregated = aggregated[:top_k]
        
        return [{"retrieval_score": score, **doc} for doc, score in aggregated]


class RAGSystem:
    
    def __init__(self, openai_client, data_dir: str = "data"):
        self.client = openai_client
        self.retriever = HybridRetriever(data_dir=data_dir)
        self.query_expander = QueryExpander(openai_client)
        self.data_dir = Path(data_dir)
        
    def load_knowledge_base(self, documents: Dict[str, str], chunk_size: int = 500, overlap: int = 50):
        self.retriever.index_documents(documents, chunk_size, overlap)
        
    def generate_answer(self, query: str, context: List[Dict], system_prompt: str) -> str:
        context_str = "\n\n".join([f"[Source: {doc['source']}, Chunk {doc['chunk_idx']}]\n{doc['text']}" for doc in context])
        
        augmented_prompt = f"""{system_prompt}

## Retrieved Context:
{context_str}

## User Query:
{query}

Please answer the query based on the context provided above."""
        
        messages = [{"role": "user", "content": augmented_prompt}]
        response = self.client.chat.completions.create(model="gpt-4o-mini", messages=messages, temperature=0.7)
        return response.choices[0].message.content
    
    def query(self, query: str, system_prompt: str, method: str = "hybrid_rerank", top_k: int = 5, expand_query: bool = False, **kwargs) -> Dict:
        context = self.retriever.retrieve(query, method=method, top_k=top_k, expand_query=expand_query, query_expander=self.query_expander if expand_query else None, **kwargs)
        answer = self.generate_answer(query, context, system_prompt)
        return {"answer": answer, "context": context, "method": method, "query": query}
