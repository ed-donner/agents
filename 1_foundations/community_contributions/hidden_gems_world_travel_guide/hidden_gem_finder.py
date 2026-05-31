import os
import openai
from dotenv import load_dotenv
from pathlib import Path
import time

# Load API key from .env
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

# Configuration
MODEL = "gpt-5-nano"
COUNTRIES_BY_CONTINENT = {
    "Africa": ["Algeria", "Angola", "Kenya"],  # Expand as needed
    "Europe": ["France", "Slovenia", "Greece"],
    "Asia": ["Japan", "Bhutan", "India"],
    "Oceania": ["Fiji", "New Zealand", "Australia"],
    "Americas": ["Peru", "Dominica", "United States"]
}

OUTPUT_DIR = Path("hidden_gems_output")
OUTPUT_DIR.mkdir(exist_ok=True)

PROMPT_TEMPLATE = """
Create a Markdown-formatted travel guide with **10 tourist sites or experiences** in {country}. Include both iconic landmarks and hidden gems (less visited but culturally rich, off-the-beaten-path, locally beloved, or highly rated yet unknown internationally).

For each site, include the following metadata:
- Name
- Location (region, continent, country, latitude and longitude)
- Description
- Key features
- Unique features distinguishing it from other sites
- Transportation access
- Ideal visiting season
- Cost estimate (USD/local currency)
- Accessibility information
- Nearby lodging
- Booking guidelines
- Safety information
- Travel tips
- Best time to visit
- Weather conditions
- Local customs and traditions
- Local cuisine
- Local culture
- Local language
- Local currency

Output the content as a single Markdown section, structured clearly under the country’s name.
"""

def query_openai(country):
    prompt = PROMPT_TEMPLATE.format(country=country)
    print(f"\nQuerying data for {country}...")
    try:
        response = openai.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"Failed for {country}: {e}")
        return f"### {country}\nFailed to fetch data."

def generate_guides():
    for continent, countries in COUNTRIES_BY_CONTINENT.items():
        filename = OUTPUT_DIR / f"{continent.lower()}_guide.md"
        with open(filename, "w", encoding="utf-8") as f:
            f.write(f"# Hidden Gems Travel Guide – {continent}\n\n")
            for country in countries:
                content = query_openai(country)
                f.write(content + "\n\n")
                time.sleep(1.5)  # Avoid hitting rate limits
        print(f"Saved {continent} guide to {filename}")

if __name__ == "__main__":
    generate_guides()
