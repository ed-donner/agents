
from langchain_openai import  OpenAIEmbeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document
import os

from dotenv import load_dotenv


load_dotenv(override=True)

MODEL = "gpt-4.1-nano"
DB_NAME = str("vector_db")

# embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
embeddings = OpenAIEmbeddings(model="text-embedding-3-large", 
base_url=os.getenv("OPENROUTER_BASE_URL"), api_key=os.getenv("OPENROUTER_API_KEY"))
RETRIEVAL_K = 5 # number of documents to retrieve 10 is the default



vectorstore = Chroma(persist_directory=DB_NAME, embedding_function=embeddings)
retriever = vectorstore.as_retriever(search_kwargs={"k": RETRIEVAL_K})



def fetch_context(question: str) -> list[Document]:
    """
    Retrieve relevant context documents for a question.
    """
    return retriever.invoke(question)




