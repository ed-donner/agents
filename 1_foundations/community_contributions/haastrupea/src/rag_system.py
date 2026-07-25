import chromadb


class RAGSystem:
    chunk_size = 500
    chunk_overlap = 50
    def __init__(self, db_path: str, collection = "knowledge_base", chunk_size: int = None, chunk_overlap: int= None) -> None:
    
        self.collection_name = collection
        self.db_path = db_path

        self.chromadb_client = chromadb.PersistentClient(path=str(db_path / "vector_store"))

        if chunk_size:
            self.chunk_size = chunk_size

        if chunk_overlap:
            self.chunk_overlap = chunk_overlap

    def prepare_chunk(self, text: str) -> list[str]:
        size = self.chunk_size
        overlap = self.chunk_overlap

        print(f"Indexing documents with chunk size={size}, overlap={overlap}")

        bag_of_words = text.split()

        chunks = []
        total_word = len(bag_of_words)
        next_chunk_start = size - overlap
        for i in range(0, total_word, next_chunk_start):
            chunk_stop = i + size
            chunk = ' '.join(bag_of_words[i:chunk_stop])
            if chunk:
                chunks.append(chunk)
        return chunks

    def setup_db_documents(self, docs: dict[str, str]):
        collection_name = self.collection_name
        all_chunks = []
        for doc_id, content in docs.items():
            chunks = self.prepare_chunk(content)
            for idx, chunk in enumerate(chunks):
                all_chunks.append({ "id": f"{doc_id}_{idx}",  "text": chunk,  "source": doc_id, "chunk_idx": idx })
        
        self.documents = all_chunks
        
        if not all_chunks:
            raise ValueError("No text chunks created from documents. Please check your document content.")
        
        try:
            self.chromadb_client.delete_collection(collection_name)
        except:
            pass
        
        self.collection = self.chromadb_client.create_collection(name=collection_name, metadata={"hnsw:space": "cosine"})
        
        batch_size = 100
        for i in range(0, len(all_chunks), batch_size):
            batch = all_chunks[i:i + batch_size]
            self.collection.add(
                docs=[doc["text"] for doc in batch],
                ids=[doc["id"] for doc in batch],
                metadatas=[{"source": doc["source"], "chunk_idx": doc["chunk_idx"]} for doc in batch]
            )
    

    def retrieve(self, query: str, top_k: int = 10):
        if self.collection is None:
            return []
        
        results = self.collection.query(query_texts=[query], n_results=top_k)
        
        print(results, "results")
        retrieved = []
        for i, doc_id in enumerate(results["ids"][0]):
            doc = next((d for d in self.documents if d["id"] == doc_id), None)
            if doc:
                distance = results["distances"][0][i]
                similarity = 1 / (1 + distance)
                retrieved.append((doc, similarity))
        all_results = {}
        for doc, score in results:
            doc_id = doc["id"]
            if doc_id not in all_results:
                all_results[doc_id] = (doc, 0.0)
                all_results[doc_id] = (doc, all_results[doc_id][1] + score)
    
        aggregated = list(all_results.values()).sort(key=lambda x: x[1], reverse=True)

        return [{"retrieval_score": score, **doc} for doc, score in aggregated[:top_k]]