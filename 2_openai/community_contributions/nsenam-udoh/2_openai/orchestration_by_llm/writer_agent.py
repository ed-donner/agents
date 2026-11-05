import re

from agents import Agent, ModelSettings, RunContextWrapper
from pydantic import BaseModel, Field

from planner_agent import MODEL_NAME

REPORT_MAX_TOKENS = 16000

INSTRUCTIONS = """
You are a senior researcher tasked with writing a cohesive report for a research
query. You will be provided with the original query, clarification answers,
research, and a numbered source list. Generate a comprehensive report based on
all of them. The final output should be lengthy, detailed markdown of at least
1000 words.
Every factual sentence in the report must end with one or more [n] citations
matching a numbered source in the numbered source list. No uncited factual
sentences are allowed. Do not write URLs. Do not cite numbers that were not
provided. Do not state facts that no source supports. If no sources were found,
state that clearly in the report.
Introductions, transitions and summaries count as factual sentences when they state
anything about the topic: cite them with [n] or remove them. Sentences that only
describe this report (for example 'This report compares ...') must be removed.
Do not describe the report itself. Do not cite a source for a sentence that the
source does not support.
"""


# shortcut: regex sentence split, abbreviations may split early, upgrade to a sentence tokenizer if needed
def uncited_sentences(markdown_report: str) -> list[str]:
    uncited = []
    in_code = False
    sentence_split = re.compile(r"(?<=[.!?])\s+")
    for line in markdown_report.splitlines():
        if line.startswith("```"):
            in_code = not in_code
            continue
        if not in_code and line.startswith("## Sources"):
            break
        if in_code or not line.strip() or line.startswith(("#", "|")):
            continue
        line = re.sub(r"^(?:[-*]|\d+\.)\s+", "", line)
        uncited.extend(
            sentence
            for sentence in sentence_split.split(line)
            if len(sentence.split()) >= 6
            and any(character.isalpha() for character in sentence)
            and not re.search(r"\[\d+\]", sentence)
        )
    return uncited


class ReportData(BaseModel):
    short_summary: str = Field(description="A short 2-3 sentence summary of the findings.")
    markdown_report: str = Field(description="The final report")
    follow_up_questions: list[str] = Field(description="Suggested topics to research further")


def writer_instructions(context: RunContextWrapper, agent: Agent) -> str:
    sources = getattr(context.context, "sources", [])
    if sources:
        source_list = "\n".join(
            f"[{number}] {source.title} - {source.url} (read {source.date_read})"
            for number, source in enumerate(sources, start=1)
        )
    else:
        source_list = "No sources found"
    return f"{INSTRUCTIONS}\n\nNumbered source list:\n{source_list}"


writer_agent = Agent(
    name="Writer Agent",
    instructions=writer_instructions,
    model=MODEL_NAME,
    model_settings=ModelSettings(max_tokens=REPORT_MAX_TOKENS),
    output_type=ReportData,
)
