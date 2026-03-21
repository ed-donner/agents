import os
from dotenv import load_dotenv
from pypdf import PdfReader

from config import Config

load_dotenv(override=True)


class DocumentIngester:
    """Reads documents from a folder, chunks and embeds them, and adds them to Chroma."""

    def __init__(
        self,
        config: Config | None = None,
        docs_folder: str = "./docs",
        chunk_size: int = 500,
        embedding_model: str = "text-embedding-3-large",
    ):
        self.cfg = config or Config()
        self.docs_folder = docs_folder
        self.chunk_size = chunk_size
        self.embedding_model = embedding_model
        self.client = self.cfg.openai
        self.collection = self.cfg.career_collection

    def read_docs_folder(self) -> list[dict]:
        """Read all PDF and TXT files from the configured docs folder."""
        all_texts = []
        if not os.path.isdir(self.docs_folder):
            return all_texts
        for file_name in os.listdir(self.docs_folder):
            file_path = os.path.join(self.docs_folder, file_name)
            if not os.path.isfile(file_path):
                continue
            text = ""
            try:
                if file_name.lower().endswith(".pdf"):
                    reader = PdfReader(file_path)
                    for page in reader.pages:
                        page_text = page.extract_text()
                        if page_text:
                            text += page_text
                elif file_name.lower().endswith(".txt"):
                    with open(file_path, "r", encoding="utf-8") as f:
                        text = f.read()
            except Exception:
                continue
            if text.strip():
                all_texts.append({"file_name": file_name, "text": text})
        return all_texts

    def chunk_text(self, text: str) -> list[str]:
        """Split text into word-based chunks of configured size."""
        words = text.split()
        chunks = []
        for i in range(0, len(words), self.chunk_size):
            chunk = " ".join(words[i : i + self.chunk_size])
            chunks.append(chunk)
        return chunks

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """Embed a list of texts using the configured OpenAI client."""
        if not texts:
            return []
        response = self.client.embeddings.create(
            model=self.embedding_model,
            input=texts,
        )
        return [item.embedding for item in response.data]

    def ingest(self) -> int:
        """
        Read docs from folder, chunk, embed, and add to Chroma.
        Returns the number of documents ingested.
        """
        docs = self.read_docs_folder()
        if not docs:
            return 0
        for doc in docs:
            chunks = self.chunk_text(doc["text"])
            ids = [f"{doc['file_name']}_chunk_{i}" for i in range(len(chunks))]

            existing = self.collection.get(ids=ids)
            existing_ids = set(existing["ids"])

            new_chunks = []
            new_ids = []
            new_meta = []

            for i, chunk in enumerate(chunks):
                chunk_id = ids[i]

                if chunk_id in existing_ids:
                    continue

                new_chunks.append(chunk)
                new_ids.append(chunk_id)
                new_meta.append({
                    "file_name": doc["file_name"],
                    "chunk": i
                })

            if not new_chunks:
                continue

            embeddings = self.embed_texts(new_chunks)

            self.collection.add(
                ids=new_ids,
                documents=new_chunks,
                metadatas=new_meta,
                embeddings=embeddings
            )
            return len(docs)


def main() -> None:
    """CLI entrypoint: run ingestion and print result."""
    ingester = DocumentIngester(docs_folder="docs")
    count = ingester.ingest()
    print(f"Ingestion complete! Ingested {count} document(s).")


if __name__ == "__main__":
    main()
