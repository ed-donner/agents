import chromadb
from chromadb.api.models.Collection import Collection
import polars as pl
from langchain_text_splitters import RecursiveCharacterTextSplitter
from sentence_transformers import SentenceTransformer, CrossEncoder
from rank_bm25 import BM25Okapi
import numpy as np
import asyncio

chromdb_persistent_path = "./chroma_db"

SEMANTIC_RETRIEVAL = "semantic_retrieval"
HYBRID_RETRIEVAL_RERANK = "hybrid_retrieval_plus_rerank"


class MedicalDiseaseQAndARetriever:
    # Chromadb is using "all-MiniLM-L6-v2" as embedding model.  That is a good choice (384 dimensions and OpenAIEmbedding do have more dimensions).
    # However, Chromadb is using L2 distance at default. Change to 'cosine' distance, a better choice than L2 one.
    # reranker_model need to match chromadb embedding model. Keep both using "all-MiniLM-L6-v2" for now
    def __init__(self, data_path: str = "data/medical_q_n_a.csv", max_semantic_cosine_distance: float = .40):
        self.shared_chroma_client = chromadb.PersistentClient(path = "./chroma_db")
        self.data_path = data_path
        # the embedding model for query need to match the embedding model for Chroma documents
        # If we ever change to use ex. OpenAI embedding for document.  We have to switch the embedding for the query too.
        # OpenAI Embedding has higher dimensions.  It should perform better in sematic search overall.
        self.embedding_model_for_query = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
        self.splitter = RecursiveCharacterTextSplitter(
                            chunk_size=500,
                            chunk_overlap=100,  # This is the key
                            separators = ["\n\n", "\n", " ", ""]
                        )
        self.identity = "medical_disease_qna"
        # chromadb is using 
        self.collection = self.shared_chroma_client.get_or_create_collection(name=self.identity, metadata={"hnsw:space": "cosine"})
        self.max_semantic_cosine_distance = max_semantic_cosine_distance
        self.hybrid_retriever = None
        
    async def setup_hybrid_retriever(self):
        self.hybrid_retriever = HybridRetriever(self.collection, embedding_model_for_query=self.embedding_model_for_query, alpha = 0.6)
        
    def batch_add_documents(self, pl_df: pl.DataFrame, batch_size= 400):
        n = pl_df.shape[0]

        for st_idx in range(0, n, batch_size):
            e_idx = min(st_idx + batch_size - 1, n - 1)
            # the default ClosedInterval = 'both' for is_between
            nested_chunks = pl_df.filter(pl.col('index').is_between(st_idx, e_idx)).select(['chunks']).to_series().to_list()
            meta_summary = pl_df.filter(pl.col('index').is_between(st_idx, e_idx)).select(['qtype', 'Question']).to_dicts()
            nested_metas = [[meta] * len(nested_chunks[i]) for i, meta in enumerate(meta_summary)]  # duplicate metas
            # flatten nested_chunks and nested_metas and ids need to take starting_index into consideration otherwise id won't be unique 
            self.collection.add(
                documents=[ x for xs in nested_chunks for x in xs ],
                metadatas=[ x for xs in nested_metas for x in xs ],
                # index-1 based
                ids=[f'{st_idx + idx + 1}_{c_idx + 1}' for idx in range(len(nested_chunks)) for c_idx in range(len(nested_chunks[idx]))],
            )

    def load_index_documents(self):
        pl_qna = pl.read_csv(self.data_path)
        pl_qna_index = pl_qna.with_row_index("index")
        pl_qna_all = pl_qna_index.with_columns(pl.col("Answer").map_elements(self.splitter.split_text, return_dtype=pl.List(pl.String)).alias("chunks"))
        self.batch_add_documents(pl_qna_all)

    def retrieve_semantic(self, query: str, n_results: int) -> str:
        embedding = self.embedding_model_for_query.encode(query)
        results = self.collection.query(query_embeddings=[embedding.astype(float)], n_results=n_results)
        # print("Retrieve semantic")
        # print(results)
        documents = results['documents'][0][:]
        distances = results['distances'][0][:]
        return [doc for doc, dist in zip(documents, distances) if dist < self.max_semantic_cosine_distance]
        
    def retrieve(self, query: str, k = 3, strategy = SEMANTIC_RETRIEVAL) -> list[str] | None:
        if strategy == SEMANTIC_RETRIEVAL:
            return self.retrieve_semantic(query, k)
        return self.hybrid_retriever.retrieve(query, k)


class MedicalDeviceManualsRetriever:
    def __init__(self, data_path: str = "data/medical_device_manuals.csv", max_semantic_cosine_distance: float = .45):
        self.shared_chroma_client = chromadb.PersistentClient(path = "./chroma_db")
        self.data_path = data_path
        self.embedding_model_for_query = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
        self.identity = "medical_device_manuals"
        # chromadb is using L2 distance in default
        self.collection = self.shared_chroma_client.get_or_create_collection(name=self.identity, metadata={"hnsw:space": "cosine"})
        self.max_semantic_cosine_distance = max_semantic_cosine_distance
        self.hybrid_retriever = None
      
    async def setup_hybrid_retriever(self):
        self.hybrid_retriever = HybridRetriever(self.collection, embedding_model_for_query=self.embedding_model_for_query, alpha = 0.6)

    def load_index_documents(self):
        pl_device= pl.read_csv(self.data_path)
        # Filter out rows with no Manufacturer
        pl_device_index = pl_device.filter(pl.col('Manufacturer').is_not_null()).with_row_index("index")
        pl_device_partial = pl_device_index.with_columns((pl.col('index') + 1).cast(pl.Utf8).alias('doc_id'))
        # Polars tries very hard not to use Pandas style apply because it is very heavy
        pl_device_all = pl_device_partial.with_columns(pl.when(pl.col("Contraindications").is_not_null()).
        then('Device: ' + pl.col("Device_Name") + ', Model: ' + pl.col("Model_Number") + ', Manufacturer: ' + pl.col("Manufacturer") + '; ' + 
            pl.col("Indications_for_Use") + ' '+  pl.col("Contraindications")).
        otherwise('Device: ' + pl.col("Device_Name") + ', Model: ' + pl.col("Model_Number") + ', Manufacturer: ' + pl.col("Manufacturer") + '; ' + pl.col("Indications_for_Use")).alias("combined_text"))

        self.collection.add(
            documents=pl_device_all.select(['combined_text']).to_series().to_list(),
            metadatas=pl_device_all.select(['Manual_Version', 'Publication_Date', 'Patient_Population']).to_dicts(),
            # index-1 based
            ids=pl_device_all.select(['doc_id']).to_series().to_list(),
        )

    def retrieve_semantic(self, query: str, n_results: int) -> str:
        embedding = self.embedding_model_for_query.encode(query)
        results = self.collection.query(query_embeddings=[embedding.astype(float)], n_results=n_results)
        # print("Retrieve semantic")
        # print(results)
        documents = results['documents'][0][:]
        distances = results['distances'][0][:]
        return [doc for doc, dist in zip(documents, distances) if dist < self.max_semantic_cosine_distance]
        
    def retrieve(self, query: str, k = 3, strategy = SEMANTIC_RETRIEVAL) -> list[str] | None:
        if strategy == SEMANTIC_RETRIEVAL:
            return self.retrieve_semantic(query, k)
        return self.hybrid_retriever.retrieve(query, k)     


class HybridRetriever:
    def __init__(self, collection: Collection, embedding_model_for_query, alpha: float = 0.5):
        self.collection = collection
        self.embedding_model_for_query = embedding_model_for_query
        results = self.collection.get(include=['documents', 'embeddings'])
        self.documents = results['documents']
        self.embeddings = results['embeddings']
        tokenized = [doc.lower().split() for doc in self.documents]
        self.bm25 = BM25Okapi(tokenized)
        self.alpha = alpha
        self.reranker = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")

    def search_semantic_matches(self, query: str) -> list[float]:
        q_emb = self.embedding_model_for_query.encode(query)
        sem_scores = np.dot(self.embeddings, q_emb)
        # To avoid divide by zero
        return (sem_scores - sem_scores.min()) / (sem_scores.max() - sem_scores.min() + 1e-8) 

    def search_keyword_matches(self, query: str) -> list[float] | None:
        bm25_scores = np.array(self.bm25.get_scores(query.lower().split()))
        if bm25_scores.max() > 0 :
            return bm25_scores / (bm25_scores.max() + 1e-8)
        else:
            # No good keyword matches, # bm25_scores.max() is a guardrail 
            return None    
    
    def search(self, query: str, n_results) -> list[str] | None:
        norm_sem_scores = self.search_semantic_matches(query)
        norm_bm25_scores = self.search_keyword_matches(query)
        if norm_bm25_scores is None:
            return None
        combined = self.alpha * norm_sem_scores + (1 - self.alpha) * norm_bm25_scores
        # I did not set up a guardrail here. Re-ranker seems to be a better guardrail
        top_k = np.argsort(combined)[::-1][:n_results]
        
        return [self.documents[i] for i in top_k]     

    def retrieve(self, query: str, k = 3) -> list[str] | None:
        candidates = self.search(query, n_results=k * 3)
        if not candidates:
            return None
        if len(candidates) <= k:
            return candidates
        else:
            # Rerank with cross-encoder (expensive, accurate). Do that only when it is necessary. 
            # In a practice, it's like relevance check and re-rank to me
            pairs = [(query, doc) for doc in candidates]
            scores = self.reranker.predict(pairs)
            reranked = sorted(zip(candidates, scores), key=lambda x: x[1], reverse=True)
            # score > 0 is a guardrail 
            return [doc for doc, score in reranked if score > 0][:k]
    
if __name__ == "__main__":
    medical_qna_retriever = MedicalDiseaseQAndARetriever()
    # medical_qna_retriever.load_index_documents()
    asyncio.run(medical_qna_retriever.setup_hybrid_retriever())
    assert medical_qna_retriever.hybrid_retriever.documents is not None, 'documents of medical_qna_retriever should be initialized'
    assert medical_qna_retriever.hybrid_retriever.embeddings is not None, 'embeddings of medical_qna_retriever should be initialized'
    assert medical_qna_retriever.hybrid_retriever.bm25 is not None, 'bm25 of medical_qna_retriever should be initialized'
    print(f'MedicalDiseaseQAndARetriever was initialized with {len(medical_qna_retriever.hybrid_retriever.documents)}')

    medical_device_retriever = MedicalDeviceManualsRetriever() 
    # medical_device_retriever.load_index_documents()
    asyncio.run(medical_device_retriever.setup_hybrid_retriever())
    assert medical_device_retriever.hybrid_retriever.documents is not None, 'documents of medical_qna_retriever should be initialized'
    assert medical_device_retriever.hybrid_retriever.embeddings is not None, 'embeddings of medical_qna_retriever should be initialized'
    assert medical_device_retriever.hybrid_retriever.bm25 is not None, 'bm25 of medical_qna_retriever should be initialized'
    print(f'MedicalDeviceManualsRetriever was initialized with {len(medical_device_retriever.hybrid_retriever.documents)}')

    results = medical_qna_retriever.retrieve("How do patients contract hantavirus pulmonary syndrome?", strategy = HYBRID_RETRIEVAL_RERANK)
    if results:
        for result in results:
            print("\n")
            print(result)
    else:
        print("Nothing qualified to retrieve")

    results = medical_device_retriever.retrieve("What are the usage of Dialysis Machine Device?", strategy = HYBRID_RETRIEVAL_RERANK)
    if results:
        for result in results:
            print("\n")
            print(result)
    else:
        print("Nothing qualified to retrieve")    

    