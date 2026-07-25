"""Web search tool for Kigali real estate research"""

from dotenv import load_dotenv
from langchain_community.utilities import GoogleSerperAPIWrapper
from langchain.agents import Tool

load_dotenv(override=True)

serper = GoogleSerperAPIWrapper()

search_tool = Tool(
    name="web_search",
    func=serper.run,
    description=(
        "Search the web for real estate listings, property developments, "
        "and housing projects in Kigali, Rwanda. Use targeted queries "
        "including property type, area, and budget when available."
    ),
)

tools = [search_tool]
