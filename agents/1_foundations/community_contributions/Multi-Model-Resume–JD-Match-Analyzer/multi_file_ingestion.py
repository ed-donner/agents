import os
from langchain.document_loaders import (
    TextLoader,
    PyPDFLoader,
    UnstructuredWordDocumentLoader,
    UnstructuredFileLoader
)



def load_and_split_resume(file_path: str):
    """
    Loads a resume file and splits it into text chunks using LangChain.

    Args:
        file_path (str): Path to the resume file (.txt, .pdf, .docx, etc.)
        chunk_size (int): Maximum characters per chunk.
        chunk_overlap (int): Overlap between chunks to preserve context.

    Returns:
        List[str]: List of split text chunks.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    ext = os.path.splitext(file_path)[1].lower()

    # Select the appropriate loader
    if ext == ".txt":
        loader = TextLoader(file_path, encoding="utf-8")
    elif ext == ".pdf":
        loader = PyPDFLoader(file_path)
    elif ext in [".docx", ".doc"]:
        loader = UnstructuredWordDocumentLoader(file_path)
    else:
        # Fallback for other common formats
        loader = UnstructuredFileLoader(file_path)

    # Load the file as LangChain documents
    documents = loader.load()

   
    return documents
    # return [doc.page_content for doc in split_docs]
