import asyncio
from ddgs import DDGS
from typing import Optional, List
from pydantic import BaseModel, Field
from openai import AsyncOpenAI
import json
from dotenv import load_dotenv
import os
from browser_tool import BrowserTool
from templates import get_apply_link_prompt, get_cover_letter_prompt, get_job_details_prompt
load_dotenv(override=True)

class ValidJobLinks(BaseModel):
    valid_urls: list[str] = Field(..., description="List of URLs that are valid job application or job description pages for the target role.")

class JobDetails(BaseModel):
    is_valid_job_posting: bool = Field(description="True if the page is an active job listing.")
    job_title: Optional[str] = Field(description="The official job title.")
    company_name: Optional[str] = Field(description="The hiring company.")
    salary: Optional[str] = Field(description="Salary range or compensation.")
    skills: List[str] = Field(description="List of 5-10 key skills.")
    job_detail: Optional[str] = Field(description="Job description.")
    application_method: str = Field(description="One of: 'direct_form', 'application_link', 'email', 'other', 'none'.")
    application_target: Optional[str] = Field(description="The final URL where the user applies, or an email address.")
    feedback: Optional[str] = Field(description="Notes on obstacles, e.g., 'Requires login'.")

class JobHunter:
    def __init__(self):
        self.openrouter_client = AsyncOpenAI(
            base_url="https://openrouter.ai/api/v1", 
            api_key=os.getenv("OPENROUTER_API_KEY")
        )
        self.groq_client = AsyncOpenAI(
            base_url="https://api.groq.com/openai/v1", 
            api_key=os.getenv("GROQ_API_KEY")
        )
        self.browser = BrowserTool()

    async def search_jobs(self, query: str, max_results: int = 10) -> List[dict]:
        """Uses DuckDuckGo to find job listing pages based on a query. Returns a list of dicts with 'title', 'href', and 'body'. """
        with DDGS() as ddgs:
            search_results = ddgs.text(query, max_results=max_results, timelimit='m')
            return [res for res in search_results]
    
    async def get_apply_links(self, search_result_url: str, target_role: str)  -> list[str]:
        """
        Navigates to a search result page, extracts links, and uses an LLM 
        to semantically filter for actual job application pages matching the target role.
        """
        potential_links = await self.browser.extract_links_from_page(search_result_url)
        system_prompt = get_apply_link_prompt(target_role=target_role)
        try:
            response = await self.groq_client.chat.completions.parse(
                model="openai/gpt-oss-safeguard-20b",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": json.dumps(potential_links)}
                ],
                response_format=ValidJobLinks,
                temperature=0.0
            )
            return response.choices[0].message.parsed.valid_urls
        except Exception as e:
            print(f"LLM filtering failed: {e}")
            return []

    async def extract_job_details(self, url: str) -> dict:
        try:
            page_html = await self.browser.get_html_content(url)
            if not page_html:
                return {"error": "Failed to retrieve page content"}
            
            system_prompt = get_job_details_prompt()
            response = await self.groq_client.chat.completions.create(
                model="openai/gpt-oss-safeguard-20b",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": page_html}
                ],
                response_format={
                    "type": "json_schema", 
                    "json_schema": {
                        "name": "JobDetails",
                        "schema": JobDetails.model_json_schema()
                    }
                },
            )
            return json.loads(response.choices[0].message.content)
        except Exception as e:
            print(f"LLM extraction failed: {e}")
            return {"error": "LLM extraction failed"}

    async def generate_cover_letter(self, job_details: dict, applicant_name: str, applicant_background: str) -> str:
        """Uses an LLM to generate a personalized cover/application letter for a given job."""
        try:
            prompt = get_cover_letter_prompt(job_details, applicant_name, applicant_background)
            response = await self.groq_client.chat.completions.create(
                model="openai/gpt-oss-safeguard-20b",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant for job applications."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1000,
                temperature=0.3,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"Cover letter generation failed: {e}")
            return "Error: Could not generate cover letter."

async def main():
    job_hunter = JobHunter()
    await job_hunter.browser.init_playwright()
    details = await job_hunter.extract_job_details("https://careers.teksystems.com/us/en/job/JP-005899800/Sr-Engineer-AI-ML")
    cover_letter = await job_hunter.generate_cover_letter(
        details, 
        "Sodiq Alabi", 
        "Experienced AI/ML Engineer with a strong background in developing scalable machine learning solutions for enterprise clients. Skilled in Python, TensorFlow, and cloud platforms."
    )
    print("Generated Cover Letter:")
    print(cover_letter)
    await job_hunter.browser.close()

if __name__ == "__main__":
    asyncio.run(main()) 