import os, json
from psycopg_pool import ConnectionPool
from huggingface_hub import InferenceClient
from dotenv import load_dotenv


class KnowledgeStore:
    def __init__(self):
        load_dotenv(override=True)

        self.hf_token = os.getenv("HF_TOKEN")
        self.hf_client = InferenceClient(
            model="intfloat/multilingual-e5-large-instruct",
            token=self.hf_token,
        )
        self.pool = ConnectionPool(
            os.getenv("POSTGRESS_CONN_STRING"), min_size=1, max_size=5
        )

    def embed(self, texts: list[str]) -> list[list[float]]:
        result = self.hf_client.feature_extraction(texts)
        return result.tolist()

    def init_schema(self):
        with self.pool.connection() as conn:
            conn.execute("CREATE EXTENSION IF NOT EXISTS vector;")
            conn.execute("""
                CREATE TABLE IF NOT EXISTS documents (
                    id SERIAL PRIMARY KEY,
                    content TEXT,
                    embedding vector(1024),          -- Qwen3-Embedding-0.6B dim
                    meta JSONB DEFAULT '{}'::jsonb
                );
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS documents_embedding_idx
                ON documents USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
            """)

    def ingest(self, chunks: list[str], meta: dict = None):
        if not chunks:
            return
        vectors = self.embed(chunks)
        with self.pool.connection() as conn:
            with conn.cursor() as cur:
                for text, vec in zip(chunks, vectors):
                    cur.execute(
                        "INSERT INTO documents (content, embedding, meta) VALUES (%s, %s, %s)",
                        (text, str(vec), json.dumps(meta or {})),
                    )

    def search(self, question: str, k: int = 5) -> list[dict]:
        q_vec = self.embed([question])[0]
        with self.pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT content, meta, 1 - (embedding <=> %s::vector) AS score
                    FROM documents
                    ORDER BY embedding <=> %s::vector
                    LIMIT %s
                """,
                    (str(q_vec), str(q_vec), k),
                )
                cols = ["content", "meta", "score"]
                return [dict(zip(cols, row)) for row in cur.fetchall()]
