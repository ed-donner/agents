import asyncio
import os
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from typing import List, Optional
from browser_use import Agent
from browser_use.llm import ChatOpenAI as BrowserChatOpenAI

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.runnables import RunnablePassthrough
from langsmith import traceable
from langchain.callbacks.tracers import LangChainTracer
from langsmith import Client as LangSmithClient

# Load environment variables
load_dotenv()


# ----------------------
# 1. Pydantic Models
# ----------------------
class MarketInsight(BaseModel):
    title: str = Field(description="Short headline or insight")
    description: str = Field(description="Detailed description of the insight")
    sentiment: str = Field(
        description="Sentiment of the insight: Positive, Negative, or Neutral"
    )


class MarketReport(BaseModel):
    topic: str = Field(description="Research topic e.g., Electric vehicles in Kenya")
    adoption_trends: List[MarketInsight] = Field(description="Current adoption trends")
    infrastructure_gaps: List[MarketInsight] = Field(
        description="Gaps and challenges in infrastructure"
    )
    key_players: List[MarketInsight] = Field(description="Major players in the market")
    opportunities: List[MarketInsight] = Field(
        description="Business or investment opportunities"
    )
    summary: str = Field(description="Overall market insight")


# ----------------------
# 2. LangChain / Tracing Setup
# ----------------------
# Updated: Removed deprecated CallbackManager, using callbacks list directly
langsmith_client = LangSmithClient()
tracer = LangChainTracer(project_name="african-market-intel", client=langsmith_client)

llm = ChatOpenAI(model="gpt-4o", temperature=0.2, callbacks=[tracer])


sentiment_llm = ChatOpenAI(model="gpt-4o", temperature=0, callbacks=[tracer])

parser = PydanticOutputParser(pydantic_object=MarketReport)


# Browser Agent
async def scrape_african_market(topic: str) -> str:
    """Scrape the web for African market information on a topic."""
    try:
        agent = Agent(
            task=(
                f"Search news, reports, and data on '{topic}' in African markets. "
                "Summarize top findings in plain text, covering adoption trends, infrastructure gaps, key players, and opportunities."
            ),
            llm=BrowserChatOpenAI(model="gpt-4o", temperature=0),
            use_vision=False,
            save_conversation_path=None,
            generate_gif=False,
        )
        result = await agent.run()
        if not result:
            raise ValueError("Agent returned empty results.")
        return str(result)
    except Exception as e:
        print(f"Error during scraping: {str(e)}")
        raise


# Analysis Prompt & Chain
analysis_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are an African market intelligence analyst. "
            "Convert raw search results into structured insights. "
            "Provide actionable and factual insights based on reliable sources. "
            "IMPORTANT: You must determine the 'sentiment' (Positive, Negative, or Neutral) for EVERY insight based on the text. "
            "{format_instructions}",
        ),
        (
            "human",
            "Raw research data:\n{raw_results}\n"
            "Extract and organize adoption trends, infrastructure gaps, key players, and opportunities.",
        ),
    ]
)


def build_analysis_chain():
    base_chain = (
        RunnablePassthrough.assign(
            format_instructions=lambda _: parser.get_format_instructions()
        )
        | analysis_prompt
        | llm
        | parser
    )
    return base_chain


# Format Report
def format_market_report(report: MarketReport) -> str:
    lines = [f"# African Market Intelligence Report: {report.topic}\n"]

    def format_section(title, insights):
        lines.append(f"## {title}\n")
        if not insights:
            lines.append("No specific insights found.\n")
            return
        for i, insight in enumerate(insights, 1):
            lines.append(
                f"{i}. {insight.title}\n   {insight.description}\n   Sentiment: {insight.sentiment}\n"
            )

    format_section("Adoption Trends", report.adoption_trends)
    format_section("Infrastructure Gaps", report.infrastructure_gaps)
    format_section("Key Players", report.key_players)
    format_section("Opportunities", report.opportunities)

    lines.append(f"## Summary\n{report.summary}")
    return "\n".join(lines)


# Full Pipeline
@traceable(name="african-market-pipeline")
async def run_pipeline(topic: str):
    try:
        print(f"Starting scraping for topic: {topic}...")
        raw_results = await scrape_african_market(topic)
        print("Scraping complete. Running analysis chain...\n")

        chain = build_analysis_chain()

        report: MarketReport = await chain.ainvoke(
            {"raw_results": raw_results}, config={"callbacks": [tracer]}
        )

        full_report = format_market_report(report)
        print(full_report)
        return full_report

    except Exception as e:
        print(f"Pipeline failed: {str(e)}")
        # Re-raise if you want the script to exit with error code, or handle gracefully
        raise


if __name__ == "__main__":
    try:
        topic = input(
            "Enter African market topic (e.g., Electric vehicles in Kenya): "
        ).strip()
        if not topic:
            print("Topic cannot be empty.")
        else:
            asyncio.run(run_pipeline(topic))
    except KeyboardInterrupt:
        print("\nProcess interrupted by user.")
    except Exception as e:
        print(f"\nFatal error: {e}")
