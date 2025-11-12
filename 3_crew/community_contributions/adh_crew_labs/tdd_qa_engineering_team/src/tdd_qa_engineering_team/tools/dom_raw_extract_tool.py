import asyncio
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout
from crewai.tools import BaseTool
from typing import Type
from pydantic import BaseModel, Field
import asyncio
from playwright.async_api import async_playwright

async def fetch_gradio_app(url, wait_time=10000, additional_wait=3000):
    """
    Fetch a Gradio app and return full HTML after page is fully loaded.
    
    Args:
        url (str): The URL of the Gradio app
        wait_time (int): Maximum time to wait for page load (milliseconds)
        additional_wait (int): Additional time to wait for dynamic content (milliseconds)
    
    Returns:
        str: Full HTML content of the loaded page
    """
    async with async_playwright() as p:
        # Launch browser in headless mode
        browser = await p.chromium.launch(headless=True)
        
        # Create a new context with viewport
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        )
        
        page = await context.new_page()
        
        try:
            print(f"Fetching: {url}")
            
            # Navigate to the URL and wait for load state
            await page.goto(url, wait_until='networkidle', timeout=wait_time)
            print("Page loaded (networkidle)")
            
            # Wait for Gradio-specific elements
            try:
                await page.wait_for_selector('.gradio-container', timeout=wait_time)
                print("Gradio container found")
            except PlaywrightTimeout:
                print("Gradio container not found, continuing anyway")
            
            # Wait for document to be ready
            await page.wait_for_load_state('domcontentloaded')
            await page.wait_for_load_state('load')
            print("Document fully loaded")
            
            # Additional wait for dynamic content
            await asyncio.sleep(additional_wait / 1000)
            
            # Scroll to trigger lazy-loaded content
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await asyncio.sleep(1)
            await page.evaluate("window.scrollTo(0, 0)")
            await asyncio.sleep(1)
            
            # Remove all script tags if requested
            html_without_scripts = await page.evaluate("""
                () => {
                    const clone = document.cloneNode(true);
                    const scripts = clone.querySelectorAll('script');
                    scripts.forEach(script => script.remove());
                    return clone.documentElement.outerHTML;
                }
            """)
            return html_without_scripts
            
        except Exception as e:
            print(f"Error fetching Gradio app: {str(e)}")
            raise
            
        finally:
            await context.close()
            await browser.close()

class DomExtractRawToolInput(BaseModel):
    """Input schema for DomExtractTool."""
    url: str = Field(..., description="Application Url")

class DomExtractRawTool(BaseTool):
    name: str = "Dom Extract Tool"
    description: str = (
        """Extracts clean structured DOM elements from a website URL.
            Returns a JSON string representation including page title, meta tags,
            full DOM tree, and all interactive elements (links, forms, buttons).
            
            Args:
                url: The website URL to analyze
            
            Returns:
                JSON string with DOM structure, metadata, and element statistics"
            )
        """
    )
    args_schema: Type[BaseModel] = DomExtractRawToolInput

    async def _run(self, url: str) -> str:
        return await fetch_gradio_app(url, 1000, 3000)