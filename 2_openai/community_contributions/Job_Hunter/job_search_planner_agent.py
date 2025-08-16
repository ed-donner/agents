from pydantic import BaseModel, Field
from job_search_agent import search_agent
from resume_parser_agent import resume_parser_agent
from job_matcher_agent import matcher_agent
from agents import Agent

print("🔧 [PLANNER AGENT] Job search planner agent module loaded")

# number of searches to perform
HOW_MANY_SEARCHES = 4

# base instructions for the agent
INSTRUCTIONS = (
    "You are an expert headhunter specializing in matching candidates to highly relevant job opportunities. "
    "Follow these steps in order: "
    "1) First, use the ResumeParserTool to analyze the candidate's resume text and extract key skills, experience, and qualifications. "
    "2) Based on the parsed resume data and job preferences, generate exactly 4 highly targeted web search queries that combine: "
    "   - relevant job titles from the resume "
    "   - related skills or technologies "
    "   - target industry "
    "   - location preferences "
    "   - seniority level "
    "3) Use the JobSearchTool to execute each search query and find actual job postings. "
    "Always use your tools to gather information before creating the final search plan. "
    "Return the search queries with reasoning for each one, along with summaries of your analysis and search results."
)


# structured output for search plan with job results
class WebSearchItem(BaseModel):
    reason: str = Field(description="Your reasoning for why this search is important to the job search.")
    query: str = Field(description="The search term to use for the web search.")

class WebSearchPlan(BaseModel):
    searches: list[WebSearchItem] = Field(description="A list of web searches to perform to best answer the job search.")
    resume_analysis: str = Field(description="Summary of key insights from resume analysis")
    job_results_summary: str = Field(description="Summary of job search results found")
    


# Converting agents as tools
print("🔧 [PLANNER AGENT] Converting agents to tools...")
search_tool = search_agent.as_tool(
    tool_name="JobSearchTool",
    tool_description="A tool for searching job postings using web search.",
)
print("✅ [PLANNER AGENT] Search agent converted to tool")

resume_parser_tool = resume_parser_agent.as_tool(
    tool_name="ResumeParserTool", 
    tool_description="A tool for analyzing resume text and extracting key skills, experience, and qualifications.",
)
print("✅ [PLANNER AGENT] Resume parser agent converted to tool")

# create the agent with the defined instructions and output types
print("🔧 [PLANNER AGENT] Initializing job search planner agent...")
planner_agent = Agent(
    name="JobSearchPlannerAgent",
    instructions=INSTRUCTIONS,
    tools=[resume_parser_tool, search_tool], # Resume parser first, then search
    handoffs=[matcher_agent],  # Handoff to matcher agent after search
    model ="gpt-4o-mini",
    output_type=WebSearchPlan,
)
print("✅ [PLANNER AGENT] Job search planner agent initialized successfully")