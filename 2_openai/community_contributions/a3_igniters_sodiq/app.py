import gradio as gr
from agents import Agent, Runner, trace, function_tool
from ddgs import DDGS
from dotenv import load_dotenv

load_dotenv(override=True)

@function_tool
def search_web(query: str, clarifications: str = "") -> str:
    """Searches the web via DuckDuckGo using the original query plus user clarifications."""
    search_term = f"{query} {clarifications}".strip()
    print(f"--- [Tool Call] Searching DuckDuckGo for: '{search_term}' ---")
 
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(search_term, max_results=5))
 
        if not results:
            return f"No results found for '{search_term}'."
 
        formatted = f"Search results for: '{search_term}'\n\n"
        for i, r in enumerate(results, 1):
            formatted += f"{i}. **{r['title']}**\n"
            formatted += f"   {r['body']}\n"
            formatted += f"   Source: {r['href']}\n\n"
 
        return formatted.strip()
 
    except Exception as e:
        return f"Error searching DuckDuckGo: {e}"

researcher_agent = Agent(
    name="Researcher",
    instructions="Use the search_web tool to find facts. Incorporate user clarifications into your search.",
    tools=[search_web],
    model="gpt-4o-mini",
)

clarifier_agent = Agent(
    name="Clarifier",
    instructions="Your job is to provide exactly 3 clarifying questions to help narrow down a research topic. Be concise.",
    model="gpt-4o-mini",
)

clarifier_tool = clarifier_agent.as_tool(
    tool_name="clarifier_tool",
    tool_description="Use this tool to get clarifying questions about a research topic."
)

MANAGER_INSTRUCTIONS = """
You are the Manager of a research team. Your job is to first ask the user for their research topic, 
then use the Clarifier tool to generate 3 clarifying questions to better understand the user's needs. 
After receiving the clarifications, you will use the Researcher tool to conduct a deep-dive web search on the topic based on the original query and the clarifications provided by the user. 
Finally, you will synthesize the information and present it in a clear and concise manner.
"""

manager_agent = Agent(
    name="Manager",
    instructions=MANAGER_INSTRUCTIONS,
    tools=[clarifier_tool],
    handoffs=[researcher_agent],
    model="gpt-4o-mini"
)


async def chat(user_input, history):
    messages = [{"role": h["role"], "content": h["content"]} for h in history]
    messages.append({"role": "user", "content": user_input})

    with trace("Research Agent Conversation"):
        result = await Runner.run(
            manager_agent,
            input=messages,
        )
    return result.final_output

ui = gr.ChatInterface(
    fn=chat,
    title="Agentic Research Team",
    description="Ask me anything, I'll clarify your needs before doing a deep-dive research.",
    type="messages"
)

if __name__ == "__main__":
    ui.launch()