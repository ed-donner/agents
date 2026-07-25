from playwright.async_api import async_playwright
from langchain_community.agent_toolkits import PlayWrightBrowserToolkit
from langchain_community.agent_toolkits import FileManagementToolkit
from langchain_community.tools.wikipedia.tool import WikipediaQueryRun
from langchain_community.utilities.wikipedia import WikipediaAPIWrapper
from langchain_community.utilities import GoogleSerperAPIWrapper
from langchain_experimental.tools import PythonREPLTool
from langchain.agents import Tool
from dotenv import load_dotenv
from datetime import datetime, timedelta
import requests
import json
import os

load_dotenv(override=True)

# ============================================================
# Config
# ============================================================

pushover_token = os.getenv("PUSHOVER_TOKEN")
pushover_user = os.getenv("PUSHOVER_USER")
pushover_url = "https://api.pushover.net/1/messages.json"
serper_key = os.getenv("SERPER_API_KEY")

# ============================================================
# 1. Playwright browser tools (async — opened once per session)
# ============================================================

async def playwright_tools():
    playwright = await async_playwright().start()
    browser = await playwright.chromium.launch(headless=False)
    toolkit = PlayWrightBrowserToolkit.from_browser(async_browser=browser)
    return toolkit.get_tools(), browser, playwright

# ============================================================
# 2. Serper Google search
# ============================================================

try:
    serper = GoogleSerperAPIWrapper()
except Exception:
    serper = None

def serper_search(query: str) -> str:
    """Search Google for a query and return the top results. Use this for researching topics, trends, and facts."""
    if serper is None:
        return "Google search unavailable — SERPER_API_KEY not set. Use duckduckgo_search instead."
    return serper.run(query)

# ============================================================
# 3. DuckDuckGo search (free, no API key)
# ============================================================

def duckduckgo_search(query: str) -> str:
    """Search DuckDuckGo for a query. Free backup search engine — use when you want a second opinion or Serper is unavailable."""
    try:
        from duckduckgo_search import DDGS
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=5))
            if not results:
                return "No results found."
            output = ""
            for r in results:
                output += f"Title: {r['title']}\nURL: {r['href']}\nSnippet: {r['body']}\n\n"
            return output.strip()
    except ImportError:
        return "Error: duckduckgo-search package not installed. Run: pip install duckduckgo-search"

# ============================================================
# 4. YouTube search (uses Serper video search)
# ============================================================

def youtube_search(query: str) -> str:
    """Search YouTube for videos related to a query. Returns titles, channels, and links. Use this to find trending videos or reference material."""
    try:
        url = "https://google.serper.dev/videos"
        payload = json.dumps({"q": query})
        headers = {"X-API-KEY": serper_key, "Content-Type": "application/json"}
        response = requests.post(url, headers=headers, data=payload, timeout=10)
        data = response.json()
        videos = data.get("videos", [])[:5]
        if not videos:
            return "No videos found."
        output = ""
        for v in videos:
            title = v.get("title", "No title")
            link = v.get("link", "No link")
            channel = v.get("channel", "Unknown")
            output += f"Title: {title}\nChannel: {channel}\nURL: {link}\n\n"
        return output.strip()
    except Exception as e:
        return f"YouTube search failed: {e}"

# ============================================================
# 5. Wikipedia
# ============================================================

def get_wikipedia_tool():
    wikipedia = WikipediaAPIWrapper()
    return WikipediaQueryRun(api_wrapper=wikipedia)

# ============================================================
# 6. Python REPL
# ============================================================

def get_python_repl():
    return PythonREPLTool()

# ============================================================
# 7. File tools (sandbox)
# ============================================================

def get_file_tools():
    toolkit = FileManagementToolkit(root_dir="sandbox")
    return toolkit.get_tools()

# ============================================================
# 8. Pushover notification
# ============================================================

def push(text: str) -> str:
    """Send a push notification to the user. Use when a draft is ready or an important update needs attention."""
    requests.post(pushover_url, data={"token": pushover_token, "user": pushover_user, "message": text})
    return "Push notification sent successfully."

# ============================================================
# 9. HTTP GET (generic — any public API)
# ============================================================

def http_get(url: str) -> str:
    """Make an HTTP GET request to any public URL or API endpoint and return the response. Use for fetching data from REST APIs, RSS feeds, or raw web content."""
    try:
        response = requests.get(url, timeout=10, headers={"User-Agent": "ContentCreatorSidekick/1.0"})
        content_type = response.headers.get("Content-Type", "")
        if "json" in content_type:
            return json.dumps(response.json(), indent=2)[:3000]
        return response.text[:3000]
    except Exception as e:
        return f"HTTP GET failed: {e}"

# ============================================================
# 10. Datetime tool
# ============================================================

def get_datetime_info(query: str) -> str:
    """Get current date/time information or do date math. Examples: 'now', 'what day is 30 days from now', 'what week number is it'. Just pass a natural description of what you need."""
    now = datetime.now()
    info = f"Current date and time: {now.strftime('%Y-%m-%d %H:%M:%S')}\n"
    info += f"Day of week: {now.strftime('%A')}\n"
    info += f"Week number: {now.isocalendar()[1]}\n"
    info += f"7 days from now: {(now + timedelta(days=7)).strftime('%Y-%m-%d %A')}\n"
    info += f"30 days from now: {(now + timedelta(days=30)).strftime('%Y-%m-%d %A')}\n"
    return info

# ============================================================
# 11. Word / character counter
# ============================================================

def count_words_and_chars(text: str) -> str:
    """Count the number of words and characters in a piece of text. Use this to check if content meets platform limits (Twitter: 280 chars, LinkedIn: ~3000 chars, etc.)."""
    words = len(text.split())
    chars = len(text)
    chars_no_spaces = len(text.replace(" ", ""))
    lines = text.count("\n") + 1
    return (
        f"Words: {words}\n"
        f"Characters (with spaces): {chars}\n"
        f"Characters (no spaces): {chars_no_spaces}\n"
        f"Lines: {lines}\n"
        f"\nPlatform limits for reference:\n"
        f"- Twitter/X: 280 characters\n"
        f"- LinkedIn post: ~3,000 characters\n"
        f"- Instagram caption: 2,200 characters\n"
        f"- YouTube description: 5,000 characters\n"
        f"- TikTok caption: 2,200 characters"
    )

# ============================================================
# 12. Hashtag generator
# ============================================================

def generate_hashtags(topic: str) -> str:
    """Generate relevant hashtags for a given topic or set of keywords. Pass the main topic or comma-separated keywords. Use this before finalizing social media posts."""
    keywords = [k.strip().lower() for k in topic.replace(",", " ").split() if len(k.strip()) > 2]
    seen = set()
    hashtags = []
    for kw in keywords:
        tag = "#" + kw.replace(" ", "").replace("-", "").replace("_", "")
        if tag not in seen:
            seen.add(tag)
            hashtags.append(tag)
    generic = ["#trending", "#viral", "#fyp", "#contentcreator", "#mustwatch"]
    for g in generic:
        if g not in seen:
            hashtags.append(g)
    return f"Generated hashtags ({len(hashtags)}):\n{' '.join(hashtags[:15])}"


# ============================================================
# Bundle everything
# ============================================================

async def other_tools():
    """Return all non-browser tools as a list."""

    tool_serper = Tool(
        name="google_search",
        func=serper_search,
        description="Search Google for a query. Use for researching topics, trends, news, and facts."
    )

    tool_ddg = Tool(
        name="duckduckgo_search",
        func=duckduckgo_search,
        description="Search DuckDuckGo for a query. Free backup search — use when you want a second source."
    )

    tool_youtube = Tool(
        name="youtube_search",
        func=youtube_search,
        description="Search YouTube for videos. Returns titles, channels, and links."
    )

    tool_push = Tool(
        name="send_push_notification",
        func=push,
        description="Send a push notification to the user when a draft is ready."
    )

    tool_http = Tool(
        name="http_get",
        func=http_get,
        description="Make an HTTP GET request to any public URL or API. Returns the response text or JSON."
    )

    tool_datetime = Tool(
        name="datetime_info",
        func=get_datetime_info,
        description="Get current date/time, day of week, week number, and date math."
    )

    tool_counter = Tool(
        name="word_character_counter",
        func=count_words_and_chars,
        description="Count words and characters in text. Use to check platform limits (Twitter 280 chars, LinkedIn 3000, etc.)."
    )

    tool_hashtags = Tool(
        name="hashtag_generator",
        func=generate_hashtags,
        description="Generate hashtags from a topic or keywords for social media posts."
    )

    wiki_tool = get_wikipedia_tool()
    python_repl = get_python_repl()
    file_tools = get_file_tools()

    return file_tools + [
        tool_serper,
        tool_ddg,
        tool_youtube,
        tool_push,
        tool_http,
        tool_datetime,
        tool_counter,
        tool_hashtags,
        wiki_tool,
        python_repl,
    ]
