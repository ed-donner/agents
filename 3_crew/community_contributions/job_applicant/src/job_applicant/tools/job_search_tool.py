import asyncio
import random
import time
import json
from typing import Optional
from crewai.tools import BaseTool
from pydantic import Field


USER_AGENTS = [
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
]


class JobSearchTool(BaseTool):
    """Searches multiple job platforms for relevant job postings using Playwright browser automation."""

    name: str = "job_search"
    description: str = (
        "Searches for job postings across LinkedIn, Indeed, Glassdoor, and ZipRecruiter. "
        "Input should be a JSON string with keys: 'keywords' (list of search terms), "
        "'locations' (list of locations), 'platforms' (list of platforms to search), "
        "and optionally 'max_results_per_platform' (default 25). "
        "Returns a JSON list of job postings with title, company, location, description, url, and platform."
    )

    def _run(self, search_params: str) -> str:
        try:
            params = json.loads(search_params)
        except json.JSONDecodeError:
            return "Error: Input must be a valid JSON string. Example: {\"keywords\": [\"python developer\"], \"locations\": [\"Remote\"]}"

        keywords = params.get("keywords", [])
        locations = params.get("locations", ["Remote"])
        platforms = params.get("platforms", ["linkedin", "indeed", "glassdoor", "ziprecruiter"])
        max_results = params.get("max_results_per_platform", 25)

        if not keywords:
            return "Error: 'keywords' list is required."

        try:
            results = asyncio.get_event_loop().run_until_complete(
                self._search_all_platforms(keywords, locations, platforms, max_results)
            )
        except RuntimeError:
            results = asyncio.run(
                self._search_all_platforms(keywords, locations, platforms, max_results)
            )

        if not results:
            return "No job postings found. Try broadening your search keywords or locations."

        return json.dumps(results, indent=2)

    async def _search_all_platforms(
        self, keywords: list, locations: list, platforms: list, max_results: int
    ) -> list:
        all_jobs = []

        for platform in platforms:
            try:
                if platform == "linkedin":
                    jobs = await self._search_linkedin(keywords, locations, max_results)
                elif platform == "indeed":
                    jobs = await self._search_indeed(keywords, locations, max_results)
                elif platform == "glassdoor":
                    jobs = await self._search_glassdoor(keywords, locations, max_results)
                elif platform == "ziprecruiter":
                    jobs = await self._search_ziprecruiter(keywords, locations, max_results)
                else:
                    continue

                all_jobs.extend(jobs)
            except Exception as e:
                all_jobs.append({
                    "title": f"[Search Error on {platform}]",
                    "company": "N/A",
                    "location": "N/A",
                    "description": f"Failed to search {platform}: {str(e)}",
                    "url": "",
                    "platform": platform,
                    "error": True,
                })

        return all_jobs

    async def _search_linkedin(self, keywords: list, locations: list, max_results: int) -> list:
        from playwright.async_api import async_playwright

        jobs = []
        query = " ".join(keywords)
        location = locations[0] if locations else "Remote"

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(user_agent=random.choice(USER_AGENTS))
            page = await context.new_page()

            try:
                url = f"https://www.linkedin.com/jobs/search/?keywords={query}&location={location}&f_TPR=r604800"
                await page.goto(url, wait_until="domcontentloaded", timeout=30000)
                await asyncio.sleep(random.uniform(2, 4))

                # Scroll to load more results
                for _ in range(min(3, max_results // 10)):
                    await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                    await asyncio.sleep(random.uniform(1.5, 3))

                job_cards = await page.query_selector_all(".base-card")

                for card in job_cards[:max_results]:
                    try:
                        title_el = await card.query_selector(".base-search-card__title")
                        company_el = await card.query_selector(".base-search-card__subtitle")
                        location_el = await card.query_selector(".job-search-card__location")
                        link_el = await card.query_selector("a.base-card__full-link")

                        title = (await title_el.inner_text()).strip() if title_el else "Unknown"
                        company = (await company_el.inner_text()).strip() if company_el else "Unknown"
                        loc = (await location_el.inner_text()).strip() if location_el else "Unknown"
                        link = await link_el.get_attribute("href") if link_el else ""

                        if title and title != "Unknown":
                            jobs.append({
                                "title": title,
                                "company": company,
                                "location": loc,
                                "description": "",
                                "requirements": [],
                                "url": link.split("?")[0] if link else "",
                                "platform": "linkedin",
                                "salary_range": None,
                                "posted_date": None,
                            })
                    except Exception:
                        continue

                # Fetch descriptions for top jobs
                for job in jobs[:10]:
                    if job["url"]:
                        try:
                            await page.goto(job["url"], wait_until="domcontentloaded", timeout=15000)
                            await asyncio.sleep(random.uniform(1, 2))

                            desc_el = await page.query_selector(".description__text")
                            if desc_el:
                                job["description"] = (await desc_el.inner_text()).strip()[:3000]
                        except Exception:
                            continue

            except Exception as e:
                jobs.append({
                    "title": "[LinkedIn Search Error]",
                    "company": "N/A",
                    "location": "N/A",
                    "description": f"Error: {str(e)}",
                    "url": "",
                    "platform": "linkedin",
                    "error": True,
                })
            finally:
                await browser.close()

        return jobs

    async def _search_indeed(self, keywords: list, locations: list, max_results: int) -> list:
        from playwright.async_api import async_playwright

        jobs = []
        query = " ".join(keywords)
        location = locations[0] if locations else "Remote"

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(user_agent=random.choice(USER_AGENTS))
            page = await context.new_page()

            try:
                url = f"https://www.indeed.com/jobs?q={query}&l={location}&fromage=7"
                await page.goto(url, wait_until="domcontentloaded", timeout=30000)
                await asyncio.sleep(random.uniform(2, 4))

                job_cards = await page.query_selector_all(".job_seen_beacon, .jobsearch-ResultsList > li")

                for card in job_cards[:max_results]:
                    try:
                        title_el = await card.query_selector("h2.jobTitle a, .jobTitle > a")
                        company_el = await card.query_selector("[data-testid='company-name'], .companyName")
                        location_el = await card.query_selector("[data-testid='text-location'], .companyLocation")

                        title = (await title_el.inner_text()).strip() if title_el else ""
                        company = (await company_el.inner_text()).strip() if company_el else "Unknown"
                        loc = (await location_el.inner_text()).strip() if location_el else "Unknown"
                        link = await title_el.get_attribute("href") if title_el else ""

                        if link and not link.startswith("http"):
                            link = f"https://www.indeed.com{link}"

                        if title:
                            jobs.append({
                                "title": title,
                                "company": company,
                                "location": loc,
                                "description": "",
                                "requirements": [],
                                "url": link,
                                "platform": "indeed",
                                "salary_range": None,
                                "posted_date": None,
                            })
                    except Exception:
                        continue

                # Fetch descriptions for top jobs
                for job in jobs[:10]:
                    if job["url"]:
                        try:
                            await page.goto(job["url"], wait_until="domcontentloaded", timeout=15000)
                            await asyncio.sleep(random.uniform(1, 2))

                            desc_el = await page.query_selector("#jobDescriptionText")
                            if desc_el:
                                job["description"] = (await desc_el.inner_text()).strip()[:3000]
                        except Exception:
                            continue

            except Exception as e:
                jobs.append({
                    "title": "[Indeed Search Error]",
                    "company": "N/A",
                    "location": "N/A",
                    "description": f"Error: {str(e)}",
                    "url": "",
                    "platform": "indeed",
                    "error": True,
                })
            finally:
                await browser.close()

        return jobs

    async def _search_glassdoor(self, keywords: list, locations: list, max_results: int) -> list:
        from playwright.async_api import async_playwright

        jobs = []
        query = "-".join(keywords)
        location = locations[0] if locations else "Remote"

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(user_agent=random.choice(USER_AGENTS))
            page = await context.new_page()

            try:
                url = f"https://www.glassdoor.com/Job/{location}-{query}-jobs-SRCH_IL.0,{len(location)}_KO{len(location)+1},{len(location)+1+len(query)}.htm"
                await page.goto(url, wait_until="domcontentloaded", timeout=30000)
                await asyncio.sleep(random.uniform(2, 5))

                job_cards = await page.query_selector_all("[data-test='jobListing'], .react-job-listing")

                for card in job_cards[:max_results]:
                    try:
                        title_el = await card.query_selector("a[data-test='job-link'], .job-title")
                        company_el = await card.query_selector(".EmployerProfile_compactEmployerName__LE242, .job-search-key-l2wjgv")
                        location_el = await card.query_selector("[data-test='emp-location'], .location")

                        title = (await title_el.inner_text()).strip() if title_el else ""
                        company = (await company_el.inner_text()).strip() if company_el else "Unknown"
                        loc = (await location_el.inner_text()).strip() if location_el else "Unknown"
                        link = await title_el.get_attribute("href") if title_el else ""

                        if link and not link.startswith("http"):
                            link = f"https://www.glassdoor.com{link}"

                        if title:
                            jobs.append({
                                "title": title,
                                "company": company,
                                "location": loc,
                                "description": "",
                                "requirements": [],
                                "url": link,
                                "platform": "glassdoor",
                                "salary_range": None,
                                "posted_date": None,
                            })
                    except Exception:
                        continue

            except Exception as e:
                jobs.append({
                    "title": "[Glassdoor Search Error]",
                    "company": "N/A",
                    "location": "N/A",
                    "description": f"Error: {str(e)}",
                    "url": "",
                    "platform": "glassdoor",
                    "error": True,
                })
            finally:
                await browser.close()

        return jobs

    async def _search_ziprecruiter(self, keywords: list, locations: list, max_results: int) -> list:
        from playwright.async_api import async_playwright

        jobs = []
        query = " ".join(keywords)
        location = locations[0] if locations else "Remote"

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(user_agent=random.choice(USER_AGENTS))
            page = await context.new_page()

            try:
                url = f"https://www.ziprecruiter.com/jobs-search?search={query}&location={location}&days=7"
                await page.goto(url, wait_until="domcontentloaded", timeout=30000)
                await asyncio.sleep(random.uniform(2, 4))

                job_cards = await page.query_selector_all(".job_content, article.job-listing")

                for card in job_cards[:max_results]:
                    try:
                        title_el = await card.query_selector("h2.job_title a, .job_title a")
                        company_el = await card.query_selector(".job_org, .t_org_link")
                        location_el = await card.query_selector(".job_location, .t_location_link")

                        title = (await title_el.inner_text()).strip() if title_el else ""
                        company = (await company_el.inner_text()).strip() if company_el else "Unknown"
                        loc = (await location_el.inner_text()).strip() if location_el else "Unknown"
                        link = await title_el.get_attribute("href") if title_el else ""

                        if title:
                            jobs.append({
                                "title": title,
                                "company": company,
                                "location": loc,
                                "description": "",
                                "requirements": [],
                                "url": link,
                                "platform": "ziprecruiter",
                                "salary_range": None,
                                "posted_date": None,
                            })
                    except Exception:
                        continue

            except Exception as e:
                jobs.append({
                    "title": "[ZipRecruiter Search Error]",
                    "company": "N/A",
                    "location": "N/A",
                    "description": f"Error: {str(e)}",
                    "url": "",
                    "platform": "ziprecruiter",
                    "error": True,
                })
            finally:
                await browser.close()

        return jobs
