
import os
import asyncio

from dotenv import load_dotenv

from agents import Runner


from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings

from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

from pusher import ResumeData

from email_agent import email_agent
from surfer import surfer_agent

# Constants
load_dotenv(override=True)

MODEL_OPENAI = "gpt-4o-mini"
LOCAL_MODEL_OPENAI = "gpt-oss:20b"

DB = "resume_db"

def read_pdf_file(file_path):
    if file_path.endswith(".pdf"):
        loader = PyPDFLoader(file_path)

        resume = loader.load()

        return resume
    else:
        return None

def load_to_store(resume):
    if resume is None:
        raise ValueError("Resume not loaded")

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=100
    )
    
    chunks = text_splitter.split_documents(resume)

    embeddings = HuggingFaceEmbeddings(
        model_name="all-MiniLM-L6-v2"
    )

    if os.path.exists(DB):
        Chroma(
            persist_directory=DB,
            embedding_function=embeddings
        ).delete_collection()

    vectorstore = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=DB
    )

    print(f"Vectorstore created with {vectorstore._collection.count()} documents")

    return vectorstore

async def surf_resume(job_description: str, vectorstore: Chroma) -> ResumeData:
    agent = surfer_agent(job_description, vectorstore)
    print("Surfing resume...")
    result = await Runner.run(
        agent,
        f"I need a cover letter for this job: \n{job_description}"
    )
    print("Resume surfed")
    return result

async def send_email(resume_data: ResumeData) -> None:
    print("Writing email...")
    result = await Runner.run(
        email_agent,
        resume_data,
    )
    print("Email sent")
    return result



async def main():
    resume_path = input("Enter the path to the resume file: ")

    resume = read_pdf_file(resume_path)

    job_description = input("Enter the job description: ")

    vectorstore = load_to_store(resume)

    surf = await surf_resume(job_description, vectorstore)
    await send_email(surf)

if __name__ == "__main__":
    asyncio.run(main())
