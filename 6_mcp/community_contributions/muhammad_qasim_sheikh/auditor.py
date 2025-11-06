from typing import Optional, Tuple
import datetime as dt
from dataclasses import asdict
from openai import OpenAI
from audits import ReadabilityScores, SEOMetrics, ToneScores, PlagiarismSignals, AuditResult, grade_from_scores
from database import write_audit, write_log
from templates import system_instructions, report_template
import asyncio
import json
import re

def strip_html(html: str) -> Tuple[str, Optional[str], Optional[str]]:
    title = None
    m = re.search(r"<title>(.*?)</title>", html, re.I|re.S)
    if m:
        title = re.sub(r"\s+", " ", m.group(1)).strip()
    m2 = re.search(r"<meta[^>]*name=\"description\"[^>]*content=\"(.*?)\"", html, re.I|re.S)
    desc = m2.group(1).strip() if m2 else None
    text = re.sub(r"<script[\s\S]*?</script>|<style[\s\S]*?</style>", " ", html, flags=re.I)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text, title, desc


from seo_audit_server import (
    compute_readability as _readability,
    compute_seo as _seo,
    compute_tone as _tone,
    compute_plagiarism_signal as _plag
)

def run_audit(url: str, html: str, target_keywords: Optional[list] = None) -> int:
    text, title, meta = strip_html(html)

    read = asyncio.run(_readability.run({"text": text}))
    seo = asyncio.run(_seo.run({"text": text, "title": title, "meta_description": meta}))
    tone = asyncio.run(_tone.run({"text": text}))
    plag = asyncio.run(_plag.run({"text": text, "top_k": 3}))

    r = ReadabilityScores(**read.structured_content)
    s = SEOMetrics(**seo.structured_content)
    t = ToneScores(**tone.structured_content)
    p = PlagiarismSignals(
        similarity_index=plag.structured_content.get("similarity_index", 0.0),
        matched_sources=plag.structured_content.get("matched_sources", []),
    )
    overall = grade_from_scores(r, s, t, p)

    kw_display = ", ".join([f"{k} ({v:.2%})" for k, v in list(s.keyword_density.items())[:10]]) or "—"

    rec_parts = []
    if r.flesch_reading_ease < 60:
        rec_parts.append("Increase readability: shorter sentences, simpler words.")
    if t.passive_voice_ratio > 0.15:
        rec_parts.append("Reduce passive voice; prefer active constructions.")
    if s.word_count < 600:
        rec_parts.append("Increase content depth (aim 800–1200 words).")
    if p.similarity_index > 0.2:
        rec_parts.append("Rewrite duplicated/boilerplate sections to lower similarity.")
    if not rec_parts:
        rec_parts.append("Looks solid. Consider adding outbound/internal links and schema.")
    recommendations = "\n- ".join([""] + rec_parts)

    client = OpenAI()
    model_prompt = f"""
    You are an SEO content analyst. Analyze the following web content for quality, tone, and engagement.
    Provide a professional paragraph summarizing the content's strengths and weaknesses.

    --- Content ---
    Title: {title}
    Meta Description: {meta}
    Body Text: {text[:4000]}  # Truncate for safety
    """

    ai_summary = ""
    try:
        resp = client.responses.create(
            model="o3-mini",
            input=model_prompt
        )
        ai_summary = resp.output_text
    except Exception as e:
        ai_summary = f"(AI summary unavailable: {e})"


    report_md = report_template().format(
        url=url,
        title=title or "(untitled)",
        fetched=dt.datetime.utcnow().isoformat(),
        grade=overall,
        read_fre=r.flesch_reading_ease,
        read_smog=r.smog,
        read_dc=r.dale_chall,
        read_grade=r.grade_level,
        seo_wc=s.word_count,
        seo_kw=kw_display,
        seo_title=title or "—",
        seo_desc=meta or "—",
        tone_sent=f"{t.sentiment:+.2f}",
        tone_form=f"{t.formality:.2f}",
        tone_passive=f"{t.passive_voice_ratio:.2f}",
        plag_sim=f"{p.similarity_index:.2f}",
        plag_sources=p.matched_sources or "—",
        recommendations=recommendations + "\n\n### AI Summary\n" + ai_summary
    )

  
    row = {
        "url": url,
        "title": title,
        "fetched_at": dt.datetime.utcnow().isoformat(), 
        "input_chars": len(text),
        "readability": asdict(r),  
        "seo": asdict(s),           
        "tone": asdict(t),           
        "plagiarism": asdict(p),    
        "overall_grade": overall,
        "report_md": report_md
    }
    aid = write_audit(row)
    write_log("audit", "INFO", f"Audit stored id={aid} url={url} grade={overall}")
    return aid
