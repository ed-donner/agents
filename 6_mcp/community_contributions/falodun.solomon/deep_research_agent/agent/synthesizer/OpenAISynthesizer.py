import os
from openai import AsyncOpenAI


class OpenAISynthesizer:

    def __init__(self):
        self.client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    async def synthesize(self, query, state):

        # Combine content
        combined_text = "\n\n".join([
            f"Source ({s['url']}):\n{s['content'][:1000]}"
            for s in state.sources
        ])

        prompt = f"""
        You are a research analyst.

        Query:
        {query}

        Sources:
        {combined_text}

        Provide:
        1. Summary
        2. Key insights
        3. Comparison (if applicable)
        4. Final recommendation
        """

        response = await self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "user", "content": prompt}
            ],
            temperature=0.3
        )

        return response.choices[0].message.content