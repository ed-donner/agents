import os
from datetime import datetime
from dotenv import load_dotenv
from crewai import Agent, Task, Crew, Process
from crewai.tools import tool
from crewai_tools import SerperDevTool
from langchain_openai import ChatOpenAI
from langchain_community.tools import DuckDuckGoSearchRun
from typing import Tuple
import yfinance as yf

load_dotenv()

llm = ChatOpenAI(model="gpt-4o", temperature=0.2)

OUTPUT_DIR = "reports"
os.makedirs(OUTPUT_DIR, exist_ok=True)

search_tool = SerperDevTool()


@tool("Yahoo Finance Tool")
def yahoo_finance_tool(ticker: str) -> str:
    """Fetch stock price, fundamentals, and analyst recommendations for a given ticker symbol."""
    stock = yf.Ticker(ticker)
    info = stock.info
    recommendations = stock.recommendations
    return (
        f"Company: {info.get('longName', 'N/A')}\n"
        f"Sector: {info.get('sector', 'N/A')}\n"
        f"Current Price: {info.get('currentPrice', 'N/A')}\n"
        f"Market Cap: {info.get('marketCap', 'N/A')}\n"
        f"P/E Ratio: {info.get('trailingPE', 'N/A')}\n"
        f"52W High: {info.get('fiftyTwoWeekHigh', 'N/A')}\n"
        f"52W Low: {info.get('fiftyTwoWeekLow', 'N/A')}\n"
        f"Analyst Recommendations:\n{recommendations.head(5).to_string() if recommendations is not None else 'N/A'}"
    )


# Guardrails
def validate_research_output(output) -> Tuple[bool, str]:
    text = output.raw if hasattr(output, "raw") else str(output)
    if len(text.strip()) < 100:
        return (False, "Research output is too short. Expand with more findings.")
    forbidden = ["I cannot", "I don't know", "no information available"]
    for phrase in forbidden:
        if phrase.lower() in text.lower():
            return (False, f"Output contains a non-answer phrase: '{phrase}'. Retry with more research.")
    return (True, text)

def validate_analysis_output(output) -> Tuple[bool, str]:
    text = output.raw if hasattr(output, "raw") else str(output)
    missing = []
    if "|" not in text:
        missing.append("a markdown table for financial data")
    if "outlook" not in text.lower() and "recommendation" not in text.lower():
        missing.append("an investment outlook or recommendation section")
    if missing:
        return (False, f"Analysis is incomplete. Missing: {', '.join(missing)}.")
    return (True, text)


# Agents
researcher = Agent(
    role="Financial Researcher",
    goal="Search the web for the latest financial news and market sentiment on a given stock or topic.",
    backstory="You are a seasoned financial journalist who digs deep into market trends and news.",
    tools=[search_tool, yahoo_finance_tool],
    llm=llm,
    verbose=True,
)

analyst = Agent(
    role="Financial Analyst",
    goal="Analyze stock fundamentals, price data, and news to produce a clear investment summary.",
    backstory="You are a CFA-level analyst who turns raw financial data into actionable insights with tables and bullet points.",
    tools=[yahoo_finance_tool],
    llm=llm,
    verbose=True,
)


research_task = Task(
    description=(
        "Search for the latest news, market sentiment, and analyst opinions on {topic}. "
        "Summarize key findings in bullet points. Include sources where possible."
    ),
    expected_output="A detailed bullet-point summary of recent news and market sentiment with at least 5 findings.",
    agent=researcher,
    guardrail=validate_research_output,
)

analysis_task = Task(
    description=(
        "Using the research findings, analyze the financials of {topic}. "
        "Present stock price, fundamentals, and analyst recommendations in markdown tables. "
        "Include bullet points for key risks and catalysts. "
        "Conclude with an investment outlook paragraph."
    ),
    expected_output=(
        "A full markdown report containing:\n"
        "- At least one markdown table with financial data\n"
        "- Bullet points for risks and catalysts\n"
        "- An investment outlook or recommendation section"
    ),
    agent=analyst,
    context=[research_task],
    guardrail=validate_analysis_output,
)


crew = Crew(
    agents=[researcher, analyst],
    tasks=[research_task, analysis_task],
    process=Process.sequential,
    verbose=True,
)


def save_report(topic: str, content: str) -> str:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_topic = topic.replace(" ", "_").replace("(", "").replace(")", "").lower()
    filename = os.path.join(OUTPUT_DIR, f"{safe_topic}_{timestamp}.md")
    with open(filename, "w", encoding="utf-8") as f:
        f.write(f"# Finance Report: {topic}\n")
        f.write(f"_Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}_\n\n")
        f.write("---\n\n")
        f.write(content)
    return filename


if __name__ == "__main__":
    topic = input("Enter a stock or company to analyze (e.g. Tesla, AAPL): ").strip()

    if not topic:
        raise ValueError("Topic cannot be empty.")

    print(f"\nRunning finance analysis for: {topic}\n")
    result = crew.kickoff(inputs={"topic": topic})

    report_content = str(result)
    output_file = save_report(topic, report_content)

    print(f"\nReport saved to: {output_file}")
