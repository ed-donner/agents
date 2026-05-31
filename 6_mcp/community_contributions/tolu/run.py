import os
import requests
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

# OpenRouter setup
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY"),
)

SERPER_API_KEY = os.getenv("SERPER_API_KEY")

def web_search(query):
    url = "https://google.serper.dev/search"
    headers = {"X-API-KEY": SERPER_API_KEY}
    response = requests.post(url, json={"q": query}, headers=headers)
    data = response.json()

    results = []
    for item in data.get("organic", [])[:3]:
        results.append(item.get("snippet", ""))

    return "\n".join(results)

def generate_runbook(issue):
    context = web_search(issue)

    prompt = f"""
Issue:
{issue}

Context from web search:
{context}

Create a short DevOps runbook with steps.
"""

    response = client.chat.completions.create(
        model="openai/gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}]
    )

    return response.choices[0].message.content

if __name__ == "__main__":
    print(generate_runbook("kubernetes pods crashing"))