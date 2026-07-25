import os
import json
from openai import AsyncOpenAI


class OpenAIReflectionEngine:

    def __init__(self):
        self.client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    async def reflect(self, query, state):

        sources_summary = "\n\n".join([
            f"URL: {s['url']}\nContent: {s['content'][:500]}"
            for s in state.sources
        ])

        prompt = f"""
        You are a research agent evaluating completeness of gathered information.

        Query:
        {query}

        Current Findings:
        {sources_summary}

        Answer in STRICT JSON:
        {{
            "enough": true or false,
            "missing_topics": ["list of missing aspects"]
        }}
        """

        response = await self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "user", "content": prompt}
            ],
            temperature=0.2
        )

        content = response.choices[0].message.content

        try:
            return json.loads(content)
        except Exception:
            # fallback safety
            return {"enough": True, "missing_topics": []}