from crewai.tools import BaseTool
from typing import Type
from pydantic import BaseModel, Field
import asyncio
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
import json

async def get_dom_with_js(url: str) -> str:
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto(url, timeout=30000)
        html = await page.content()
        await browser.close()
        return html

def element_to_dict(element):
    """Recursively converts a BeautifulSoup element to a JSON-friendly dict."""
    if element.name is None:
        return element.strip() if element.strip() else None

    return {
        "tag": element.name,
        "attributes": element.attrs,
        "children": [
            child for child in
            (element_to_dict(c) for c in element.contents)
            if child is not None
        ]
    }

def dom_to_json_full(html: str) -> str:
    """Converts full HTML DOM to JSON tree."""
    soup = BeautifulSoup(html, "html.parser")
    body = soup.body or soup  # default to soup if no body
    dom_dict = element_to_dict(body)
    return json.dumps(dom_dict, ensure_ascii=False)       

class DomExtractToolInput(BaseModel):
    """Input schema for DomExtractTool."""
    url: str = Field(..., description="Application Url")

class DomExtractTool(BaseTool):
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
    args_schema: Type[BaseModel] = DomExtractToolInput

    async def _run(self, url: str) -> str:
        dom = await get_dom_with_js(url)
        return dom_to_json_full(dom)