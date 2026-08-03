
import os

from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader



def read_pdf_file(file_path):
    if file_path.endswith(".pdf"):
        loader = PyPDFLoader(file_path)

        resume = loader.load()

        return resume
    else:
        return None

def load_to_store(resume, vectorstore, resume_id: str):
    if resume is None:
        raise ValueError("Resume not loaded")

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=100
    )

    chunks = text_splitter.split_documents(resume)

    # Add metadata
    for chunk in chunks:
        chunk.metadata["resume_id"] = resume_id

    vectorstore.add_documents(chunks)

    return len(chunks)


