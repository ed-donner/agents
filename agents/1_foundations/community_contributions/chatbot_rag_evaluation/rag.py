import os
from langchain_text_splitters import CharacterTextSplitter
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma

DB_NAME = 'career_db'
DIRECTORY_NAME = "knowledge_base"

class Retriever:
    def __init__(self, db_name=DB_NAME, directory_name=DIRECTORY_NAME):
        self.db_name = db_name
        self.directory_name = directory_name
        self._embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
        self._retriever = None
        self._init_or_load_db()

    def _get_documents(self):
        text_loader_kwargs = {'encoding': 'utf-8'}
        loader = DirectoryLoader(self.directory_name, glob="*.txt", loader_cls=TextLoader, loader_kwargs=text_loader_kwargs)
        documents = loader.load()
        return documents

    def _init_or_load_db(self):
        if os.path.exists(self.db_name):
            vectorstore = Chroma(persist_directory=self.db_name, embedding_function=self._embeddings)
            print("Loaded existing vectorstore.")
        else:
            documents = self._get_documents()
            text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=300)
            chunks = text_splitter.split_documents(documents)
            print(f"Total number of chunks: {len(chunks)}")

            vectorstore = Chroma.from_documents(documents=chunks, embedding=self._embeddings, persist_directory=self.db_name)
            print(f"Vectorstore created with {vectorstore._collection.count()} documents")

        self._retriever = vectorstore.as_retriever(search_kwargs={"k": 25})

    def get_relevant_chunks(self, message: str):
        docs = self._retriever.invoke(message)
        return [doc.page_content for doc in docs]
