from agents import Agent, Runner
from openai.types.responses import ResponseTextDeltaEvent


INSTRUCTIONS = """
You are a senior researcher writing a polished markdown report from a research brief and summarized web findings.

Write a detailed report that is thoughtful, structured, and readable.

Requirements:
- Start with a strong title.
- Include an executive summary near the top.
- Organize the report with meaningful section headings.
- Synthesize the evidence instead of repeating search summaries verbatim.
- Call out trends, disagreements, limitations, and practical implications where relevant.
- End with a concise conclusion and a short "Further Research" section.
- Produce at least 1000 words in markdown.
"""



class Writer:
    def __init__(self, query: str):
        self.query = query
        self.agent = Agent(
            name="Writer",
            instructions=INSTRUCTIONS,
            model="gpt-4o-mini"
        )


    async def run(self, search_results: list[str]):
        response = Runner.run_streamed(
            self.agent, f"Original query: {self.query}\n\nSummarized web findings: {"\n\n".join(search_results)}"
        )
        report = ""

        async for event in response.stream_events():
            if event.type == "raw_response_event" and isinstance(event.data, ResponseTextDeltaEvent):
                report += event.data.delta
                yield report

