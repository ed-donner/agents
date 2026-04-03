import json
from openai import OpenAI
from config import OPENAI_API_KEY, OPENROUTER_URL
from models.schema import StandardStep

client = OpenAI(base_url=OPENROUTER_URL, api_key=OPENAI_API_KEY)

def get_standards(domain: str, process_name: str) -> list[StandardStep]:
    prompt = f"""
    You are an expert in {domain} operations.
    Provide recommended process steps for '{process_name}' as a JSON list.
    Each step must include:
      - step
      - priority (high / medium / low)
    Only return valid JSON.
    """
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[{"role":"user","content":prompt}],
        temperature=0
    )
    text = response.choices[0].message.content
    try:
        data = json.loads(text)
        return [StandardStep(**item) for item in data]
    except json.JSONDecodeError:
        return []