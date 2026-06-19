import os
from pathlib import Path
from agents import Agent, Runner
from pypdf import PdfReader
from typing import Optional
from dotenv import load_dotenv
from openai import OpenAI
from pypdf import PdfReader
import gradio as gr
import asyncio

def read_pdf_file() -> Optional[str]:
    """
    Read and extract text from a PDF file located in the same directory as this script.
    
    Returns:
        Optional[str]: The extracted text content if successful, None if there's an error
    """
    try:
        # Get the current directory where the script is located
        current_dir = Path(__file__).parent
        pdf_path = current_dir / "book_proposal.pdf"
        
        # Check if file exists
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF file not found at: {pdf_path}")
        
        # Create a PDF reader object
        reader = PdfReader(pdf_path)
        
        # Get the number of pages
        num_pages = len(reader.pages)
        print(f"Total number of pages: {num_pages}")
        
        # Read all pages using list comprehension for better performance
        text_content = " ".join(page.extract_text() for page in reader.pages)
            
        return text_content
        
    except Exception as e:
        print(f"Error reading PDF file: {str(e)}")
        return None

def create_agent(prompt: str) -> Agent:
    agent = Agent(name="Book Reviewer", instructions=prompt, model="gpt-4o-mini")
    return agent

async def chat(message, history):
    result = await Runner.run(openai_agent, message)
    return result.final_output

async def main():
    content = read_pdf_file()
    system_prompt = f"You are acting as expert book proposal reviewer.\
All questions need to be answered based on the book proposal below:"

    system_prompt += f"\n\n## Proposal:\n{content}\n\n"
    system_prompt += f"With this context, please chat with the user, always keep answers short and concise."

    if content:
        print("Successfully read PDF content")
        global openai_agent
        openai_agent = create_agent(system_prompt)
        gr.ChatInterface(chat).launch()


if __name__ == "__main__":
    load_dotenv(override=True)
    asyncio.run(main())