from dotenv import load_dotenv

from playwright.async_api import async_playwright
from langchain_community.agent_toolkits import PlayWrightBrowserToolkit
from langchain_community.utilities import GoogleSerperAPIWrapper
from langchain_core.tools import tool
from langchain.agents import Tool
from urllib.parse import quote_plus
from job_search.config import NUM_OF_JOBS

load_dotenv(override=True)


@tool
async def scrape_linkedin_jobs(query: str, location: str = "") -> str:
    """
    Scrapes job listings from LinkedIn public search for the given query and location.
    Returns a list of up to NUM_OF_JOBS jobs with title, company, location, and link.
    Args:
        query: Job title / keywords (e.g. "Senior AI Engineer")
        location: Location filter (e.g. "India", "Bangalore")
    """
    url = (
        f"https://www.linkedin.com/jobs/search/"
        f"?keywords={quote_plus(query)}&location={quote_plus(location)}"
    )
    playwright = await async_playwright().start()
    browser = await playwright.chromium.launch(headless=True)
    page = await browser.new_page()
    try:
        await page.goto(url, wait_until="domcontentloaded", timeout=15000)
        await page.wait_for_selector("ul.jobs-search__results-list", timeout=10000)
        cards = await page.query_selector_all(
            "ul.jobs-search__results-list li"
        )
        results = []
        for card in cards[:NUM_OF_JOBS]:
            title_el  = await card.query_selector("h3.base-search-card__title")
            company_el = await card.query_selector("h4.base-search-card__subtitle")
            loc_el    = await card.query_selector("span.job-search-card__location")
            link_el   = await card.query_selector("a.base-card__full-link")

            title   = (await title_el.inner_text()).strip()   if title_el   else "N/A"
            company = (await company_el.inner_text()).strip() if company_el else "N/A"
            loc     = (await loc_el.inner_text()).strip()     if loc_el     else "N/A"
            link    = (await link_el.get_attribute("href"))   if link_el    else "N/A"
            if link and "?" in link:
                link = link.split("?")[0]

            results.append(f"- {title} | {company} | {loc}\n  Apply: {link}")

        return "\n\n".join(results) if results else "No listings found."
    except Exception as e:
        return f"Error scraping LinkedIn: {e}"
    finally:
        await browser.close()
        await playwright.stop()


async def playwright_tools():
    """
    Playwright tool for performing local headless/non-headless browser
    operations
    """
    playwright = await async_playwright().start()
    browser = await playwright.chromium.launch(headless=True)
    toolkit = PlayWrightBrowserToolkit.from_browser(async_browser=browser)
    return toolkit.get_tools(), browser, playwright

async def search_tool():
    """
    Serper search tool for performing web search
    """
    serper = GoogleSerperAPIWrapper()
    tool =Tool(
        name="web_search",
        func=serper.run,
        description=(
            "Use this tool when you want to get the results of an"
            " online web search"
        )
    )
    return tool

@tool
def open_jobs_in_browser(urls: list[str]) -> str:
    """
    Opens job listing URLs in the user's default browser.
    Opens the first URL in a new browser window and any additional URLs
    as new tabs in the same window.
    Args:
        urls: List of job listing URLs to open (e.g. LinkedIn job links)
    Returns:
        Confirmation message with the number of jobs opened.
    """
    import webbrowser
    if not urls:
        return "No URLs provided."
    webbrowser.open(urls[0], new=1)
    for url in urls[1:]:
        webbrowser.open(url, new=2)
    return f"Opened {len(urls)} job listing(s) in your browser."


async def add_tools():
    """
    Add tools to the assistant
    """
    return [await search_tool(), scrape_linkedin_jobs, open_jobs_in_browser]
