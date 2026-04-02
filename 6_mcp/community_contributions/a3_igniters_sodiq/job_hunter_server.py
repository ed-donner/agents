from mcp.server.fastmcp import FastMCP
from job_hunter import JobHunter

mcp = FastMCP("job_hunter_server")
job_hunter = JobHunter()


async def ensure_browser_initialized():
    """Helper to ensure the Playwright browser is started before use."""
    if not job_hunter.browser.browser:
        await job_hunter.browser.init_playwright()

@mcp.tool()
async def search_jobs(query: str, max_results: int = 10):
    """
    Search for job postings on the web.
    
    Args:
        query: The search string (e.g., 'Remote AI Engineer jobs').
        max_results: The number of search results to retrieve.

    Returns:
        List[dict]: A list of search results containing 'title', 'href', and 'body'.
    """
    await ensure_browser_initialized()
    return await job_hunter.search_jobs(query, max_results)

@mcp.tool()
async def find_application_links(url: str, target_role: str):
    """
    Analyze a specific web page to identify direct application URLs matching a target role.

    Args:
        url: The URL of the page to analyze (e.g., a search results page or company careers page).
        target_role: The specific job title or role to filter for.

    Returns:
        list[str]: A list of semantically filtered URLs pointing to actual job application pages.
    """
    await ensure_browser_initialized()
    return await job_hunter.get_apply_links(url, target_role)

@mcp.tool()
async def extract_job_details(url: str):
    """
    Scrape a specific job posting URL to extract structured professional data.

    Args:
        url: The direct URL of the job posting to analyze.

    Returns:
        dict: Structured data including 'job_title', 'company_name', 'salary', 'skills', 
              'job_detail', and 'application_method'.
    """
    await ensure_browser_initialized()
    return await job_hunter.extract_job_details(url)

@mcp.tool()
async def generate_cover_letter(job_details: dict, applicant_name: str, applicant_background: str):
    """
    Generate a tailored, professional cover letter based on job details and applicant profile.

    Args:
        job_details: A dictionary containing extracted information about the job.
        applicant_name: The full name of the job seeker.
        applicant_background: A summary of the applicant's relevant experience and skills.

    Returns:
        str: A formatted, personalized cover letter ready for application.
    """
    await ensure_browser_initialized()
    return await job_hunter.generate_cover_letter(job_details, applicant_name, applicant_background)

if __name__ == "__main__":
    mcp.run(transport='stdio')