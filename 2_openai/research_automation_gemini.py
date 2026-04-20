#!/usr/bin/env python3
"""
Deep Research Automation - Gemini Version
Replicated from OpenAI Agents SDK to work with Gemini API

Features:
- Research planning
- Web search (using free alternatives)
- Report writing  
- Email sending

Note: Uses free web search alternatives instead of OpenAI's paid WebSearchTool
"""

from dotenv import load_dotenv
from openai import OpenAI
import json
import os
import asyncio
import sendgrid
from sendgrid.helpers.mail import Mail, Email, To, Content
from typing import Dict, List
import requests
from bs4 import BeautifulSoup
import time
from pydantic import BaseModel, Field

load_dotenv(override=True)

# Setup Gemini client
gemini = OpenAI(
    api_key=os.getenv("GOOGLE_API_KEY"), 
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
)

class WebSearchItem(BaseModel):
    """Structure for a single web search"""
    reason: str = Field(description="Your reasoning for why this search is important to the query.")
    query: str = Field(description="The search term to use for the web search.")

class WebSearchPlan(BaseModel):
    """Structure for multiple web searches"""
    searches: List[WebSearchItem] = Field(description="A list of web searches to perform to best answer the query.")

class ReportData(BaseModel):
    """Structure for research report"""
    short_summary: str = Field(description="A short 2-3 sentence summary of the findings.")
    markdown_report: str = Field(description="The final report in markdown format")
    follow_up_questions: List[str] = Field(description="Suggested topics to research further")

class GeminiAgent:
    """Simple agent class to replicate OpenAI Agents SDK functionality"""
    
    def __init__(self, name: str, instructions: str, output_type=None):
        self.name = name
        self.instructions = instructions
        self.output_type = output_type
        self.client = gemini
    
    def run(self, message: str):
        """Run the agent with a message"""
        messages = [
            {"role": "system", "content": self.instructions},
            {"role": "user", "content": message}
        ]
        
        if self.output_type:
            # For structured output, we'll simulate it with JSON parsing
            enhanced_instructions = self.instructions + f"\n\nPlease respond with a valid JSON object matching this structure: {self.output_type.model_json_schema()}"
            messages[0]["content"] = enhanced_instructions
            
            response = self.client.chat.completions.create(
                model="gemini-1.5-flash",
                messages=messages
            )
            
            content = response.choices[0].message.content
            
            # Try to parse JSON from the response
            try:
                # Extract JSON from response (handle cases where model adds explanation)
                json_start = content.find('{')
                json_end = content.rfind('}') + 1
                if json_start >= 0 and json_end > json_start:
                    json_str = content[json_start:json_end]
                    parsed_data = json.loads(json_str)
                    return self.output_type(**parsed_data)
                else:
                    # Fallback: create default structure
                    return self._create_fallback_response(content)
            except Exception as e:
                print(f"Warning: Could not parse structured output, using fallback: {e}")
                return self._create_fallback_response(content)
        else:
            response = self.client.chat.completions.create(
                model="gemini-1.5-flash",
                messages=messages
            )
            return response.choices[0].message.content
    
    def _create_fallback_response(self, content: str):
        """Create fallback response for structured output"""
        if self.output_type == WebSearchPlan:
            return WebSearchPlan(searches=[
                WebSearchItem(reason="General research", query=content[:100]),
                WebSearchItem(reason="Additional context", query="related information"),
            ])
        elif self.output_type == ReportData:
            return ReportData(
                short_summary="Research completed based on available information.",
                markdown_report=content,
                follow_up_questions=["Further investigation needed", "More recent developments"]
            )
        return content

class WebSearchTool:
    """Free web search using DuckDuckGo API"""
    
    def __init__(self):
        self.base_url = "https://html.duckduckgo.com/html/"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def search(self, query: str, max_results: int = 5) -> List[Dict]:
        """Search the web using DuckDuckGo"""
        try:
            params = {'q': query}
            response = self.session.get(self.base_url, params=params, timeout=10)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                results = []
                
                for result in soup.find_all('div', class_='web-result')[:max_results]:
                    title_elem = result.find('h2')
                    snippet_elem = result.find('span', class_='result__snippet')
                    
                    if title_elem and snippet_elem:
                        results.append({
                            'title': title_elem.get_text(strip=True),
                            'snippet': snippet_elem.get_text(strip=True)[:200],
                            'query': query
                        })
                
                return results
            
        except Exception as e:
            print(f"Search error for '{query}': {e}")
            
        return [{'title': 'Search unavailable', 'snippet': f'Could not search for: {query}', 'query': query}]

class ResearchSystem:
    """Complete research automation system"""
    
    def __init__(self):
        self.search_tool = WebSearchTool()
        
        # Create agents
        self.planner_agent = GeminiAgent(
            name="Research Planner",
            instructions="""You are a helpful research assistant. Given a query, come up with a set of web searches 
to perform to best answer the query. Output 3 terms to query for. Respond with a JSON object containing 
'searches' array, where each item has 'reason' and 'query' fields.""",
            output_type=WebSearchPlan
        )
        
        self.search_agent = GeminiAgent(
            name="Search Summarizer", 
            instructions="""You are a research assistant. Given search results, you produce a concise summary. 
The summary must be 2-3 paragraphs and less than 300 words. Capture the main points. Write succinctly, 
focusing on facts. This will be consumed by someone synthesizing a report, so capture the essence and 
ignore fluff. Do not include additional commentary other than the summary itself."""
        )
        
        self.writer_agent = GeminiAgent(
            name="Report Writer",
            instructions="""You are a senior researcher tasked with writing a cohesive report for a research query. 
You will be provided with the original query, and some initial research done by a research assistant.
You should first come up with an outline for the report that describes the structure and flow of the report. 
Then, generate the report and return that as your final output.
The final output should be in markdown format, and it should be lengthy and detailed. Aim for 5-10 pages 
of content, at least 1000 words. Respond with JSON containing 'short_summary', 'markdown_report', and 'follow_up_questions'.""",
            output_type=ReportData
        )
        
        self.email_agent = GeminiAgent(
            name="Email Sender",
            instructions="""You are able to send a nicely formatted HTML email based on a detailed report.
You will be provided with a detailed report. Convert the markdown report into clean, well presented HTML 
with an appropriate subject line. Focus on clear formatting, headings, and readability."""
        )
    
    async def plan_searches(self, query: str) -> WebSearchPlan:
        """Plan which searches to run for the query"""
        print("🔍 Planning research searches...")
        result = self.planner_agent.run(f"Query: {query}")
        print(f"Will perform {len(result.searches)} searches")
        return result
    
    async def perform_search(self, search_item: WebSearchItem) -> str:
        """Perform a single web search and summarize"""
        print(f"🌐 Searching for: {search_item.query}")
        
        # Perform web search
        search_results = self.search_tool.search(search_item.query)
        
        # Format results for summarization
        formatted_results = f"Search term: {search_item.query}\nReason: {search_item.reason}\n\nResults:\n"
        for result in search_results:
            formatted_results += f"Title: {result['title']}\nSnippet: {result['snippet']}\n\n"
        
        # Summarize results
        summary = self.search_agent.run(formatted_results)
        return summary
    
    async def perform_searches(self, search_plan: WebSearchPlan) -> List[str]:
        """Perform all planned searches"""
        print("📚 Performing research searches...")
        
        tasks = [self.perform_search(search_item) for search_item in search_plan.searches]
        results = await asyncio.gather(*tasks)
        
        print("✅ Research searches completed")
        return results
    
    def write_report(self, query: str, search_results: List[str]) -> ReportData:
        """Write comprehensive research report"""
        print("📝 Writing research report...")
        
        input_text = f"Original query: {query}\n\nSummarized search results:\n"
        for i, result in enumerate(search_results, 1):
            input_text += f"\n--- Search Result {i} ---\n{result}\n"
        
        report = self.writer_agent.run(input_text)
        print("✅ Report completed")
        return report
    
    def send_email(self, report: ReportData, subject: str, from_email: str, to_email: str) -> Dict[str, str]:
        """Send research report via email"""
        try:
            # Convert report to HTML
            html_body = self.email_agent.run(report.markdown_report)
            
            sg = sendgrid.SendGridAPIClient(api_key=os.environ.get('SENDGRID_API_KEY'))
            from_email_obj = Email(from_email)
            to_email_obj = To(to_email)
            content = Content("text/html", html_body)
            mail = Mail(from_email_obj, to_email_obj, subject, content).get()
            response = sg.client.mail.send.post(request_body=mail)
            
            if response.status_code == 202:
                return {"status": "success", "message": "Research report sent successfully"}
            else:
                return {"status": "failed", "message": f"SendGrid returned {response.status_code}"}
                
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    async def run_complete_research(self, query: str, from_email: str = None, to_email: str = None, send_email: bool = False):
        """Run complete research workflow"""
        print("🚀 Starting deep research...\n")
        
        # Step 1: Plan searches
        search_plan = await self.plan_searches(query)
        
        # Step 2: Perform searches
        search_results = await self.perform_searches(search_plan)
        
        # Step 3: Write report
        report = self.write_report(query, search_results)
        
        # Step 4: Send email if requested
        email_result = None
        if send_email and from_email and to_email:
            print("📤 Sending research report...")
            subject = f"Research Report: {query}"
            email_result = self.send_email(report, subject, from_email, to_email)
            print(f"Email status: {email_result['status']}")
        
        return {
            "query": query,
            "search_plan": search_plan,
            "search_results": search_results,
            "report": report,
            "email_result": email_result
        }

async def main():
    """Main function to demonstrate the research system"""
    
    # Create research system
    research_system = ResearchSystem()
    
    # Research query
    query = "Latest AI Agent frameworks in 2025"
    
    # Run research (without sending actual email)
    result = await research_system.run_complete_research(
        query=query,
        from_email="YOUR_VERIFIED_EMAIL@example.com",  # Change this
        to_email="YOUR_EMAIL@example.com",             # Change this
        send_email=False  # Set to True to actually send email
    )
    
    print("\n" + "="*60)
    print("📊 RESEARCH RESULTS")
    print("="*60)
    print(f"🔍 Query: {result['query']}")
    print(f"\n📋 Summary: {result['report'].short_summary}")
    print(f"\n📄 Report Preview:\n{result['report'].markdown_report[:500]}...")
    print(f"\n❓ Follow-up Questions:")
    for question in result['report'].follow_up_questions:
        print(f"  • {question}")
    
    if result['email_result']:
        print(f"\n📤 Email Status: {result['email_result']['status']}")

if __name__ == "__main__":
    print("Deep Research Automation - Gemini Version")
    print("="*50)
    asyncio.run(main())
