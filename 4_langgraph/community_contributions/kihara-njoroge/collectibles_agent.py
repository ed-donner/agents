import asyncio
import os
from dotenv import load_dotenv

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.runnables import RunnablePassthrough, RunnableLambda
from langchain_core.chat_history import InMemoryChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain.callbacks.tracers import LangChainTracer
from langchain.callbacks.manager import CallbackManager
from langsmith import traceable, Client as LangSmithClient
from pydantic import BaseModel, Field
from typing import List

from browser_use import Agent
from browser_use.llm import ChatOpenAI as BrowserChatOpenAI

load_dotenv()


class Collectible(BaseModel):
    name: str = Field(description="Name of the collectible item")
    price: str = Field(description="Listed price including currency symbol")
    condition: str = Field(description="Item condition e.g. New, Used, Mint")
    rating: str = Field(description="Seller rating or N/A")


class CollectiblesReport(BaseModel):
    items: List[Collectible] = Field(description="Top collectible listings found")
    summary: str = Field(description="Brief market insight based on results")
    best_deal: str = Field(description="Name of the item offering the best value")


langsmith_client = LangSmithClient()
tracer = LangChainTracer(project_name="collectibles-agent", client=langsmith_client)
callback_manager = CallbackManager(handlers=[tracer])

llm = ChatOpenAI(
    model="gpt-4o",
    temperature=0.2,
    callback_manager=callback_manager,
)

parser = PydanticOutputParser(pydantic_object=CollectiblesReport)

analysis_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are an expert collectibles market analyst. "
            "Parse the raw browser results and extract structured data. "
            "Provide genuine market insight in the summary.\n"
            "{format_instructions}",
        ),
        (
            "human",
            "Here are the raw collectibles search results:\n{raw_results}\n"
            "Extract and structure this data.",
        ),
    ]
)

chat_history_store: dict[str, InMemoryChatMessageHistory] = {}


def get_session_history(session_id: str) -> InMemoryChatMessageHistory:
    if session_id not in chat_history_store:
        chat_history_store[session_id] = InMemoryChatMessageHistory()
    return chat_history_store[session_id]


@traceable(name="browser-scrape-collectibles")
async def scrape_collectibles() -> str:
    """Run browser agent to scrape eBay collectibles listings."""
    agent = Agent(
        task=(
            "Go to ebay.com and search for 'rare vintage collectibles'. "
            "Sort by Best Match. For the top 5 results, extract: "
            "item name, price, condition, and seller rating. "
            "Return everything as plain text."
        ),
        llm=BrowserChatOpenAI(model="gpt-4o", temperature=0),
        use_vision=False,
        save_conversation_path=None,
        generate_gif=False,
    )
    result = await agent.run()
    return str(result)


def build_analysis_chain():
    """
    LCEL chain: prompt | llm | parser
    Wrapped with RunnableWithMessageHistory for session-aware memory.
    """
    base_chain = (
        RunnablePassthrough.assign(
            format_instructions=lambda _: parser.get_format_instructions(),
        )
        | analysis_prompt
        | llm
        | parser
    )

    return RunnableWithMessageHistory(
        base_chain,
        get_session_history,
        input_messages_key="raw_results",
        history_messages_key="history",
    )


def format_report(report: CollectiblesReport) -> str:
    """Convert structured Pydantic model to readable markdown report."""
    lines = ["Collectibles Market Report\n"]
    for i, item in enumerate(report.items, 1):
        lines.append(f"{i}. {item.name}")
        lines.append(f"Price: {item.price}")
        lines.append(f"Condition: {item.condition}")
        lines.append(f"Seller Rating: {item.rating}\n")
    lines.append(f"Market Insight: {report.summary}")
    lines.append(f"Best Deal: {report.best_deal}")
    return "\n".join(lines)


@traceable(name="collectibles-pipeline")
async def run_pipeline():
    raw_results = await scrape_collectibles()
    print("Scraping complete. Running analysis chain...\n")

    chain = build_analysis_chain()
    full_chain = chain | RunnableLambda(format_report)

    report = full_chain.invoke(
        {"raw_results": raw_results},
        config={"configurable": {"session_id": "collectibles-session-1"}},
    )

    print(report)
    return report


if __name__ == "__main__":
    asyncio.run(run_pipeline())
