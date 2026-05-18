import os
import json
from datetime import datetime
from dotenv import load_dotenv
from crewai import Agent, Task, Crew, Process
from crewai.tools import tool
from crewai_tools import SerperDevTool
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from typing import Tuple

# ----------------------
# Setup
# ----------------------
load_dotenv()

if not os.getenv("OPENAI_API_KEY"):
    raise EnvironmentError("Missing OPENAI_API_KEY")

llm = ChatOpenAI(model="gpt-4o", temperature=0.2)

OUTPUT_DIR = "reports"
os.makedirs(OUTPUT_DIR, exist_ok=True)

search_tool = SerperDevTool()

# ----------------------
# LLM Sentiment Prompt
# ----------------------
sentiment_prompt = PromptTemplate(
    input_variables=["text"],
    template="""
    You are an expert news sentiment analyst.

    Classify the sentiment of the following news into:
    - Bullish (positive impact, growth, optimism)
    - Bearish (negative impact, risk, decline)
    - Neutral (mixed or unclear)

    Return ONLY valid JSON:

    {
    "sentiment": "Bullish | Bearish | Neutral",
    "confidence": number (0-100)
    }

    News:
    {text}
    """,
)


# ----------------------
# Sentiment Tool (LLM-powered)
# ----------------------
@tool("LLM News Sentiment Analyzer")
def sentiment_tool(text: str) -> str:
    """
    Uses OpenAI LLM to classify sentiment of news text.
    """
    try:
        chain = sentiment_prompt | llm
        response = chain.invoke({"text": text})

        content = response.content.strip()

        # Ensure valid JSON fallback
        try:
            parsed = json.loads(content)
            sentiment = parsed.get("sentiment", "Neutral")
            confidence = parsed.get("confidence", 50)
        except Exception:
            sentiment = "Neutral"
            confidence = 50

        return json.dumps({"sentiment": sentiment, "confidence": confidence})

    except Exception as e:
        return json.dumps({"sentiment": "Neutral", "confidence": 50, "error": str(e)})


# ----------------------
# Guardrails
# ----------------------
def validate_research_output(output) -> Tuple[bool, str]:
    text = output.raw if hasattr(output, "raw") else str(output)

    if len(text.strip()) < 150:
        return (False, "Research output too short.")

    if text.count("-") < 5:
        return (False, "Include at least 5 bullet points.")

    forbidden = ["I cannot", "I don't know", "no information available"]
    for phrase in forbidden:
        if phrase.lower() in text.lower():
            return (False, f"Invalid phrase detected: {phrase}")

    return (True, text)


def validate_analysis_output(output) -> Tuple[bool, str]:
    text = output.raw if hasattr(output, "raw") else str(output)

    missing = []

    if not any(line.strip().startswith("|") for line in text.splitlines()):
        missing.append("markdown table")

    if "outlook" not in text.lower():
        missing.append("outlook section")

    if "sentiment" not in text.lower():
        missing.append("sentiment analysis")

    if missing:
        return (False, f"Missing: {', '.join(missing)}")

    return (True, text)


# ----------------------
# Agents
# ----------------------
researcher = Agent(
    role="News Researcher",
    goal="Find the latest news and key developments on a topic.",
    backstory="You are a top investigative journalist tracking global events.",
    tools=[search_tool],
    llm=llm,
    verbose=True,
)

analyst = Agent(
    role="News Intelligence Analyst",
    goal="Turn news into structured insights, trends, and sentiment analysis.",
    backstory="You analyze global news like an intelligence agency analyst.",
    tools=[sentiment_tool],
    llm=llm,
    verbose=True,
)

# ----------------------
# Tasks
# ----------------------
research_task = Task(
    description=(
        "Search for the latest news on {topic}. Provide 5-8 bullet points.\n"
        "Each bullet must include:\n"
        "- Headline\n"
        "- 1-2 sentence summary\n"
        "- Source (if available)"
    ),
    expected_output="At least 5 detailed news bullet points.",
    agent=researcher,
    guardrail=validate_research_output,
)

analysis_task = Task(
    description=(
        "Using the research findings:\n\n"
        "1. Extract each headline and summary.\n"
        "2. Use the sentiment tool for EACH news item.\n\n"
        "3. Create a markdown table:\n"
        "| Headline | Summary | Sentiment | Confidence |\n\n"
        "4. Identify key trends (bullet points).\n"
        "5. List risks and opportunities.\n"
        "6. Provide a final OUTLOOK section.\n\n"
        "Be structured, analytical, and concise."
    ),
    expected_output=(
        "Full report with:\n"
        "- Markdown table\n"
        "- Sentiment analysis\n"
        "- Trends\n"
        "- Risks & opportunities\n"
        "- Outlook"
    ),
    agent=analyst,
    context=[research_task],
    guardrail=validate_analysis_output,
)

# ----------------------
# Crew
# ----------------------
crew = Crew(
    agents=[researcher, analyst],
    tasks=[research_task, analysis_task],
    process=Process.sequential,
    verbose=True,
)


# ----------------------
# Save Report
# ----------------------
def save_report(topic: str, content: str) -> str:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_topic = topic.replace(" ", "_").lower()

    filename = os.path.join(OUTPUT_DIR, f"{safe_topic}_{timestamp}.md")

    with open(filename, "w", encoding="utf-8") as f:
        f.write(f"# 📰 News Intelligence Report: {topic}\n")
        f.write(f"_Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}_\n\n")
        f.write("---\n\n")
        f.write(content)

    return filename


# ----------------------
# Main
# ----------------------
if __name__ == "__main__":
    topic = input("Enter a topic (e.g. AI, geopolitics, weather): ").strip()

    if not topic:
        raise ValueError("Topic cannot be empty.")

    print(f"Running analysis for: {topic}\n")

    result = crew.kickoff(inputs={"topic": topic})

    report_content = str(result)
    output_file = save_report(topic, report_content)

    print(f"\n✅ Report saved to: {output_file}")
