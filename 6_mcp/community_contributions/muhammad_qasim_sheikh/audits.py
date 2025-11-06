from dataclasses import dataclass
from typing import List, Dict, Optional
import datetime as dt

@dataclass
class ReadabilityScores:
    flesch_reading_ease: float
    smog: float
    dale_chall: float
    grade_level: float

@dataclass
class SEOMetrics:
    word_count: int
    keyword_density: Dict[str, float]
    title: Optional[str] = None
    meta_description: Optional[str] = None

@dataclass
class ToneScores:
    sentiment: float  
    formality: float  
    passive_voice_ratio: float 

@dataclass
class PlagiarismSignals:
    similarity_index: float  # 0..1
    matched_sources: List[Dict[str, str]]

@dataclass
class AuditResult:
    url: str
    title: str
    fetched_at: str
    input_chars: int
    readability: ReadabilityScores
    seo: SEOMetrics
    tone: ToneScores
    plagiarism: PlagiarismSignals
    overall_grade: str
    report_md: str



def grade_from_scores(readability: ReadabilityScores, seo: SEOMetrics, tone: ToneScores, plagiarism: PlagiarismSignals) -> str:
    score = 0.0
  
    score += min(max((readability.flesch_reading_ease / 100.0), 0), 1) * 0.30
   
    density_ok = 0.0
    if seo.keyword_density:
        top = sorted(seo.keyword_density.values(), reverse=True)[:1]
        top_density = top[0] if top else 0
        density_ok = 1.0 if 0.005 <= top_density <= 0.025 else 0.6 if 0.003 <= top_density <= 0.04 else 0.3
    score += min(seo.word_count / 1200.0, 1.0) * 0.25 + density_ok * 0.10
   
    score += (max(tone.sentiment, 0) * 0.10) + ((1 - min(tone.passive_voice_ratio, 1)) * 0.10) + (tone.formality * 0.05)
   
    score += (1 - min(plagiarism.similarity_index, 1)) * 0.10
   
    if score >= 0.90: return "A+"
    if score >= 0.80: return "A"
    if score >= 0.70: return "B"
    if score >= 0.60: return "C"
    return "D"
