from langchain_openai import ChatOpenAI
from langchain_community.tools import WikipediaQueryRun
from langchain_community.utilities import WikipediaAPIWrapper
from state import ResearchState

api_wrapper = WikipediaAPIWrapper(top_k_results=2)
wiki_tool = WikipediaQueryRun(
    name="wikipedia_search",
    description="Search Wikipedia for a given query.",
    api_wrapper=api_wrapper
)

research_agent_llm = ChatOpenAI(model="gpt-4o-mini", temperature=0).bind_tools([wiki_tool])

RESEARCH_AGENT_PROMPT = """
You are a research assistant. You have access to a Wikipedia search tool.
Your job is to:
1.  Use the `wikipedia_search` tool to find relevant information for the user's query.
2.  Read the tool's output.
3.  Produce a concise summary of the key findings, facts, and figures relevant to the query.
The summary must be around 800 words.
Do not include any additional commentary other than the summary itself.
Put the actual URLs of the documents, add them in the reference section
"""

def summarizer_agent_node(state: ResearchState) -> ResearchState:
    print("EXECUTING SUMMARIZER AGENT")

    topics = state.best_topics or state.topics or []
    summarized_results = []

    for topic in topics:
        try:
            print(f"Summarizing topic: {topic}")
            query = f"{RESEARCH_AGENT_PROMPT}\n\nUser Query: {topic}"

            response = research_agent_llm.invoke(query)
            summary = getattr(response, "content", str(response))

            if "No good Wikipedia Search results found" in summary or "Page not found" in summary:
                print(f"No results for: {query}")
                summarized_results.append(f"No information found on Wikipedia for: {query}")
                continue

            summarized_results.append(f"Topic: {topic}\nSummary: {summary.strip()}")
            print(f"Done: {topic}\n")

        except Exception as e:
            print(f"Failed to summarize '{topic}': {e}")
            summarized_results.append(f"Topic: {topic}\nSummary: No summary available (error).")

    state.research_snippets = summarized_results
    print("Research Done")
    return state


