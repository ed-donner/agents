import os
import glob
from langchain_core.documents import Document
from langchain_text_splitters import  MarkdownTextSplitter
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
from dotenv import load_dotenv
from pypdf import PdfReader


MODEL = "gpt-4.1-nano"

DB_NAME = str("vector_db")
KNOWLEDGE_BASE = str( "me")

# embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

load_dotenv(override=True)

embeddings = OpenAIEmbeddings(
    model="text-embedding-3-large", 
    base_url=os.getenv("OPENROUTER_BASE_URL"), 
    api_key=os.getenv("OPENROUTER_API_KEY")
    )

# OpenRouter: drop-in API. Get a key at https://openrouter.ai/keys
# Add OPENROUTER_API_KEY to .env (or it falls back to OPENAI_API_KEY)



def fetch_documents():
    documents = []
    for file in glob.glob(os.path.join(KNOWLEDGE_BASE, "*")):
        if file.endswith(".pdf"):
            reader = PdfReader(file)
            text = ""
            for page in reader.pages:
                t = page.extract_text()
                text = text + t if t else text

            documents.append(text)
        elif file.endswith(".txt") or file.endswith(".md"):
            with open(file, "r", encoding="utf-8") as f:
                text = f.read()
            documents.append(text)
        else:
            print(f"Skipping {file} as it is not a pdf, txt, or md file")
            continue
    return documents


def create_chunks(documents):
    # text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=200)
    text_splitter = MarkdownTextSplitter(chunk_size=1200, chunk_overlap=200)
    docs = [Document(page_content=text) for text in documents]
    chunks = text_splitter.split_documents(docs)
    return chunks


def create_embeddings(chunks):
    if os.path.exists(DB_NAME):
        Chroma(persist_directory=DB_NAME, embedding_function=embeddings).delete_collection()

    vectorstore = Chroma.from_documents(
        documents=chunks, embedding=embeddings, persist_directory=DB_NAME
    )

    collection = vectorstore._collection
    count = collection.count()

    sample_embedding = collection.get(limit=1, include=["embeddings"])["embeddings"][0]
    dimensions = len(sample_embedding)
    print(f"There are {count:,} vectors with {dimensions:,} dimensions in the vector store")
    return vectorstore


if __name__ == "__main__":
    documents = fetch_documents()
    chunks = create_chunks(documents)
    create_embeddings(chunks)
    print("Ingestion complete")
