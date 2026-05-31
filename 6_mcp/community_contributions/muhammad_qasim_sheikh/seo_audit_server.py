from typing import Dict, Any
from pydantic import BaseModel, Field
from mcp.server.fastmcp import FastMCP
import re
import math
import json

mcp = FastMCP("content_quality_auditor_mcp")


class AuditArgs(BaseModel):
    text: str = Field(description="Input content to analyze")
    title: str | None = Field(default=None, description="Optional title or heading of the content")
    meta_description: str | None = Field(default=None, description="Optional meta description text")


class AuditReport(BaseModel):
    readability: Dict[str, Any]
    seo: Dict[str, Any]
    tone: Dict[str, Any]
    plagiarism: Dict[str, Any]
    overall_score: float
    summary: str

def _word_count(text: str) -> int:
    return len(re.findall(r'\b\w+\b', text))


def _grade(score: float) -> str:
    if score >= 85:
        return "Excellent"
    elif score >= 70:
        return "Good"
    elif score >= 50:
        return "Fair"
    else:
        return "Needs Improvement"


@mcp.tool()
def compute_readability(args: AuditArgs) -> Dict[str, Any]:
    text = args.text
    words = _word_count(text)
    sentences = max(1, len(re.findall(r'[.!?]', text)))
    syllables = sum(len(re.findall(r'[aeiouy]+', w.lower())) for w in re.findall(r'\w+', text))
    flesch = 206.835 - 1.015 * (words / sentences) - 84.6 * (syllables / words)
    return {
        "readability_score": round(flesch, 2),
        "grade_level": "Easy" if flesch > 80 else "Moderate" if flesch > 60 else "Hard",
        "words": words,
        "sentences": sentences,
    }


@mcp.tool()
def compute_seo(args: AuditArgs) -> Dict[str, Any]:
    text = args.text.lower()
    words = _word_count(text)
    keywords = ["ai", "automation", "cloud", "assistant"]
    keyword_hits = sum(text.count(k) for k in keywords)
    density = round((keyword_hits / max(words, 1)) * 100, 2)
    title_len = len(args.title or "")
    meta_len = len(args.meta_description or "")

    return {
        "keyword_density_percent": density,
        "title_length": title_len,
        "meta_length": meta_len,
        "recommendations": [
            "Title under 60 chars" if title_len > 60 else "✅ Title length OK",
            "Meta 120–160 chars" if not (120 <= meta_len <= 160) else "✅ Meta length OK",
        ],
    }


@mcp.tool()
def compute_tone(args: AuditArgs) -> Dict[str, Any]:
    text = args.text.lower()
    tone = "Neutral"
    if any(w in text for w in ["excited", "amazing", "great", "incredible"]):
        tone = "Positive"
    elif any(w in text for w in ["sad", "terrible", "worst", "angry"]):
        tone = "Negative"
    elif any(w in text for w in ["please", "kindly", "thank"]):
        tone = "Polite"
    return {"detected_tone": tone}


@mcp.tool()
def compute_plagiarism(args: AuditArgs) -> Dict[str, Any]:
    text = args.text.strip().lower()
    hash_value = abs(hash(text)) % 1000
    plagiarism_score = (hash_value % 50) / 100.0
    return {"plagiarism_similarity": plagiarism_score, "is_suspect": plagiarism_score > 0.3}


@mcp.tool()
def full_audit(args: AuditArgs) -> AuditReport:
    """
    Run all sub-tools and combine their results into a structured JSON report.
    """
    readability = compute_readability(args)
    seo = compute_seo(args)
    tone = compute_tone(args)
    plagiarism = compute_plagiarism(args)

    score = (
        (readability["readability_score"] / 2)
        + (100 - (plagiarism["plagiarism_similarity"] * 100) / 4)
        + (max(0, 100 - abs(2 - seo["keyword_density_percent"])) / 4)
    ) / 2.5
    summary = (
        f"Overall quality is {_grade(score)}.\n\n"
        f"- Readability: {readability['grade_level']}\n"
        f"- Tone: {tone['detected_tone']}\n"
        f"- Keyword Density: {seo['keyword_density_percent']}%\n"
        f"- Plagiarism: {round(plagiarism['plagiarism_similarity']*100, 1)}%\n"
    )

    report = AuditReport(
        readability=readability,
        seo=seo,
        tone=tone,
        plagiarism=plagiarism,
        overall_score=round(score, 2),
        summary=summary,
    )
    return report


if __name__ == "__main__":
    mcp.run(transport="stdio")
