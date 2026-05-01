from pydantic import BaseModel, Field


class ResearchFinding(BaseModel):
    """A single key finding extracted from research literature."""
    point: str = Field(description="A concise key finding in one or two sentences.")


class ResearchResult(BaseModel):
    """
    Structured output from the Neuroscience Research Agent.
    Using a Pydantic model ensures the agent always returns parseable,
    reliably structured data instead of free-form markdown.
    """
    summary: str = Field(
        description="A plain-English summary of the research (2-4 sentences)."
    )
    findings: list[ResearchFinding] = Field(
        description="3 to 5 key findings extracted from the literature.",
        min_length=1,
        max_length=5,
    )
    citations: list[str] = Field(
        description="Full citation strings, one per paper (Author, Year, Title, Journal)."
    )
    pubmed_links: list[str] = Field(
        default_factory=list,
        description="Direct PubMed URLs for each paper, if available."
    )

    def to_markdown(self) -> str:
        """Render the structured result as formatted markdown for the UI."""
        lines = ["🔬 **Summary:**", self.summary, ""]

        lines.append("🧠 **Key Findings:**")
        for f in self.findings:
            lines.append(f"- {f.point}")
        lines.append("")

        lines.append("📚 **Citations:**")
        for i, citation in enumerate(self.citations):
            link = self.pubmed_links[i] if i < len(self.pubmed_links) else None
            lines.append(f"- {citation}" + (f" [↗]({link})" if link else ""))

        return "\n".join(lines)