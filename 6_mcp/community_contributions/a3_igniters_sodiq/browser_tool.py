from playwright.async_api import async_playwright
from bs4 import BeautifulSoup

class BrowserTool:
    """A tool that uses Playwright to navigate web pages and extract information."""

    def __init__(self):
        self.browser = None
        self.playwright = None

    async def init_playwright(self):
        """Initializes the Playwright browser."""
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(headless=True)

    async def extract_links_from_page(self, url: str) -> list[dict[str, str]]:
        """Navigates to the given URL and extracts all hyperlinks from the page. Returns a list of dictionaries with cleaned text."""
        page = await self.browser.new_page()
        try:
            await page.goto(url, wait_until="networkidle", timeout=30000)
            links_data = await page.eval_on_selector_all(
                "a", 
                "elements => elements.map(el => ({ url: el.href, text: el.textContent }))"
            )
            return [
                {"url": item["url"], "text": item["text"].strip() if item["text"] else ""}
                for item in links_data 
                if item["url"] and not item["url"].startswith("javascript:")
            ]
        except Exception as e:
            print(f"Error extracting links from {url}: {e}")
            return []
        finally:
            await page.close()

    async def get_html_content(self, url: str) -> str:
        """Navigates to the given URL and returns the full HTML content of the page."""
        page = await self.browser.new_page()
        try:
            await page.goto(url, wait_until="networkidle", timeout=30000)
            content = await page.content()
            
            soup = BeautifulSoup(content, 'html.parser')
            for element in soup(["script", "style", "nav", "footer", "header", "aside"]):
                element.decompose()
            return soup.prettify()
        except Exception as e:
            print(f"Error retrieving HTML content from {url}: {e}")
            return ""
        finally:
            await page.close()
    
    async def close(self):
        """Closes the Playwright browser."""
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
            
if __name__ == "__main__":
    async def main():
        tool = BrowserTool()
        await tool.init_playwright()
        links = await tool.extract_links_from_page("https://remoteok.com/remote-ai-jobs")
        print("Extracted links:")
        for link in links:
            print(link)

    import asyncio
    asyncio.run(main())