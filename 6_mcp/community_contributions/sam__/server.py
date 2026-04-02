import os
from dotenv import load_dotenv
from fastmcp import FastMCP
from openai import OpenAI
from langchain_community.utilities import GoogleSerperAPIWrapper

load_dotenv()

mcp = FastMCP("gpt4-mini-server")

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
serper = GoogleSerperAPIWrapper(serper_api_key=os.getenv("SERPER_API_KEY"))


@mcp.tool()
def web_search(query: str) -> str:
    """Search the web for real-time info"""
    results = serper.results(query)
    organic = results.get("organic", [])[:5]

    if not organic:
        return "No results found."

    return "\n\n".join(
        f"{item['title']}\n{item['link']}\n{item['snippet']}"
        for item in organic
    )


@mcp.tool()
def ask_gpt(prompt: str) -> str:
    """Ask GPT"""
    res = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
    )
    return res.choices[0].message.content


@mcp.tool()
def smart_search(question: str) -> str:
    """Search + GPT"""
    search = web_search(question)

    res = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "Answer using search results"},
            {"role": "user", "content": f"{question}\n\n{search}"}
        ],
    )
    return res.choices[0].message.content


if __name__ == "__main__":
    mcp.run()