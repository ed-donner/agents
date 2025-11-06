import re, math, json
from fastmcp import FastMCP
from fastmcp.tools import Tool
from typing import Optional

mcp = FastMCP("seo_audit")

def _words(text: str):
    return re.findall(r"[A-Za-z0-9']+", text.lower())

def flesch_reading_ease(text: str) -> float:
    
    words = _words(text)
    sentences = re.split(r"[.!?]+", text)
    syllables = sum(max(1, len(re.findall(r"[aeiouy]+", w))) for w in words)
    W, S = max(1, len(words)), max(1, len([s for s in sentences if s.strip()]))
    return round(206.835 - 1.015*(W/S) - 84.6*(syllables/W), 2)

def smog_index(text: str) -> float:
    polysyllables = sum(1 for w in _words(text) if len(re.findall(r"[aeiouy]+", w)) >= 3)
    S = max(1, len(re.split(r"[.!?]+", text)))
    return round(1.0430 * math.sqrt(polysyllables * (30 / S)) + 3.1291, 2)

def dale_chall(text: str) -> float:
    
    return max(4.9, 10 - min(10, flesch_reading_ease(text)/10))

def grade_level(text: str) -> float:
    fre = flesch_reading_ease(text)
    if fre >= 90: return 5
    if fre >= 80: return 6
    if fre >= 70: return 8
    if fre >= 60: return 10
    if fre >= 50: return 12
    if fre >= 30: return 14
    return 16

def keyword_density(text: str, top_n: int = 10) -> dict:
    ws = _words(text)
    total = len(ws) or 1
    from collections import Counter
    c = Counter(ws)
    top = c.most_common(top_n)
    return {k: v/total for k,v in top}

def passive_voice_ratio(text: str) -> float:
   
    return min(1.0, len(re.findall(r"\b(was|were|be|been)\b\s+[a-z]+ed\b", text.lower())) / (len(_words(text)) or 1) * 10)

def sentiment_score(text: str) -> float:
    
    pos = len(re.findall(r"\b(good|great|excellent|benefit|improve|success)\b", text, re.I))
    neg = len(re.findall(r"\b(bad|poor|fail|risk|issue|problem)\b", text, re.I))
    total = pos + neg
    return 0.0 if total == 0 else (pos - neg) / total

def formality_score(text: str) -> float:
    contractions = len(re.findall(r"\b(can't|won't|don't|I'm|it's|you're|we're)\b", text, re.I))
    return max(0.0, 1.0 - min(1.0, contractions / (len(_words(text)) or 1) * 20))

@mcp.tool()
def compute_readability(text: str) -> dict:
    return {
        "flesch_reading_ease": flesch_reading_ease(text),
        "smog": smog_index(text),
        "dale_chall": dale_chall(text),
        "grade_level": grade_level(text)
    }

@mcp.tool()
def compute_seo(text: str, title: Optional[str] = None, meta_description: Optional[str] = None, top_n: int = 10) -> dict:
    return {
        "word_count": len(_words(text)),
        "keyword_density": keyword_density(text, top_n),
        "title": title,
        "meta_description": meta_description
    }

@mcp.tool()
def compute_tone(text: str) -> dict:
    return {
        "sentiment": sentiment_score(text),
        "formality": formality_score(text),
        "passive_voice_ratio": passive_voice_ratio(text)
    }

@mcp.tool()
def compute_plagiarism_signal(text: str, top_k: int = 3) -> dict:

    lines = [l.strip() for l in text.splitlines() if len(l.strip()) > 20]
    from collections import Counter
    sim = 0.0
    if lines:
        dup_count = sum(1 for _, cnt in Counter(lines).items() if cnt > 1)
        sim = min(1.0, dup_count / len(lines))
    return {"similarity_index": sim, "matched_sources": []}

if __name__ == "__main__":
    mcp.run("stdio")
