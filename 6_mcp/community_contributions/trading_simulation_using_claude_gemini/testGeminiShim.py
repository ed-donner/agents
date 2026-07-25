# test_gemini_minimal.py
import asyncio, os
from dotenv import load_dotenv
from openai import AsyncOpenAI
from openai_compat_gemini import GeminiCompatOpenAIClient

load_dotenv(override=True)
GEMINI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai/"
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

async def main():
    raw = AsyncOpenAI(base_url=GEMINI_BASE_URL, api_key=GOOGLE_API_KEY)
    client = GeminiCompatOpenAIClient(raw)

    messages = [
        {"role": "system", "content": "You can call tools if provided."},
        {"role": "user", "content": "Say hello, then stop."},
    ]

    resp = await client.chat.completions.create(
        model="gemini-2.0-flash",  # or gemini-2.5-flash if enabled
        messages=messages,
        max_tokens=200,  # will be kept
        temperature=0.2, # will be kept
        parallel_tool_calls=True,  # <-- will be stripped
        reasoning_effort="medium", # <-- will be stripped
    )
    print("OK, got:", type(resp), "first tokens:", resp.choices[0].message.content[:60])

asyncio.run(main())
