from pydantic import BaseModel, Field
from agents import Agent

INSTRUCTIONS = (
    "You are a senior researcher producing a structured deep research report.\n"
    "You receive the original query, clarifications (Q&A), and raw search summaries.\n"
    "Produce all sections below. Write in clear markdown inside each field where noted.\n"
    "- executive_summary: 2–4 sentences for executives.\n"
    "- key_findings: bullet or short paragraphs of factual takeaways (markdown).\n"
    "- analysis: interpretation, tradeoffs, limitations, and implications (markdown, substantive).\n"
    "- sources_and_method: how material was gathered; list notable domains or source types cited in the snippets "
    "(you may infer from the excerpts; do not invent specific URLs you did not see).\n"
    "- markdown_report: one cohesive document that includes titled sections: Summary, Findings, Analysis, "
    "Sources & methodology, and optional Further research. Aim for thorough coverage (roughly 1000+ words when "
    "the material supports it).\n"
    "- short_summary: 2–3 sentences distilling the bottom line.\n"
    "- follow_up_questions: avenues for additional research."
)


class ReportData(BaseModel):
    executive_summary: str = Field(description="Brief executive-oriented summary.")
    key_findings: str = Field(description="Markdown: main factual findings from the research.")
    analysis: str = Field(description="Markdown: deeper analysis, tradeoffs, limitations.")
    sources_and_method: str = Field(description="Markdown: sources/types seen in snippets and methodology notes.")
    markdown_report: str = Field(description="Full structured deep research report in markdown.")
    short_summary: str = Field(description="A short 2–3 sentence summary of the findings.")
    follow_up_questions: list[str] = Field(description="Suggested topics to research further.")


writer_agent = Agent(
    name="WriterAgent",
    instructions=INSTRUCTIONS,
    model="gpt-4o-mini",
    output_type=ReportData,
)
