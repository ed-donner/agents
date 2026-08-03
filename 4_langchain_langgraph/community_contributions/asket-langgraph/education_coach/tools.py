from langchain_community.tools import DuckDuckGoSearchRun, WikipediaQueryRun
from langchain_community.utilities import WikipediaAPIWrapper

from education_coach.config import get_settings
from education_coach.rag import build_course_search_tool_lazy, course_materials_ready


def build_education_tools():
    settings = get_settings()
    wiki = WikipediaAPIWrapper(lang=settings.wikipedia_lang, top_k_results=2)
    tools: list = [
        WikipediaQueryRun(api_wrapper=wiki),
        DuckDuckGoSearchRun(name="web_search"),
    ]
    if course_materials_ready():
        tools.insert(0, build_course_search_tool_lazy())
    return tools
