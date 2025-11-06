import datetime as dt

def system_instructions():
    return f"""
You are a Content Quality Auditor Agent.
Your job: fetch → analyze → grade → report.
Use the provided tools via MCP servers:
- fetch: retrieve HTML for a URL (if available)
- seo_audit: compute readability, SEO metrics, tone & plagiarism signals
- memory: store brief audit summaries keyed by URL
- brave/plagiarism: (optional) enhance plagiarism signals
- mailpace: (optional) email the report markdown to the user
Follow safety: if a tool is unavailable, continue with remaining tools and produce the best possible report.
Now is {dt.datetime.utcnow().isoformat()} UTC.
""".strip()


def report_template():
    return """
# Content Quality Audit Report
**URL:** {url}
**Title:** {title}
**Fetched:** {fetched}
**Overall Grade:** {grade}

---
## Readability
- Flesch Reading Ease: **{read_fre}**
- SMOG Index: **{read_smog}**
- Dale–Chall (proxy): **{read_dc}**
- Estimated Grade Level: **{read_grade}**

## SEO
- Word Count: **{seo_wc}**
- Top Keywords (density): {seo_kw}
- Title: {seo_title}
- Meta Description: {seo_desc}

## Tone
- Sentiment: **{tone_sent}** (−1 to 1)
- Formality: **{tone_form}** (0 to 1)
- Passive Voice Ratio: **{tone_passive}** (0 to 1)

## Plagiarism Signals
- Similarity Index: **{plag_sim}** (0 to 1; lower is better)
- Matched Sources (if any): {plag_sources}

---
### Recommendations
{recommendations}
"""