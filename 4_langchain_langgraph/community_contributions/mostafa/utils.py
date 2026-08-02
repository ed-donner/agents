import requests
from bs4 import BeautifulSoup
from langchain_openai import ChatOpenAI


# ─── LLM Factory ───

def get_llm(model: str = 'gpt-4o-mini', temperature: float = 0.0):
    ''' Factory function to create LLM instances with consistent settings.'''
    return ChatOpenAI(model=model, temperature=temperature)


# ─── Content Retrieve ───

def get_content_from_url(url: str) -> str:
    """Fetches and extracts text content from a given URL."""
    try:
        print(f"Fetching content from: {url}")
        page = requests.get(url, timeout=10)
        print(f"Received response with status code: {page.status_code}")
        page.raise_for_status()  # Raise an error for bad status codes

        print("Parsing content...")
        soup = BeautifulSoup(page.content, 'html.parser')
        for tag in soup(['script', 'style', 'nav', 'footer', 'header', 'aside']):
            tag.decompose()
        content = soup.get_text(separator=' ', strip=True)
        return content
    except Exception as e:
        print(f"Error fetching content from {url}: {e}")
        return f'Failed to retrieve content: {e}'

