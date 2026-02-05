"""
Governance Research Agent - Standalone Gradio App

An AI-powered research assistant for analysing corporate governance documents
with forensic-grade citations and provenance tracking.
"""

import gradio as gr
import asyncio
import json
import os
import hashlib
import re
import math
from pathlib import Path
from typing import Optional, List, Dict, Set, Tuple, Literal
from collections import Counter
from dotenv import load_dotenv

load_dotenv()

import fitz
from agents import Agent, Runner, function_tool, trace, gen_trace_id
from pydantic import BaseModel, Field

ASSETS_DIR = Path(__file__).parent / "assets"

PDF_FILES = [
    {"filename": "BHP_16AR.pdf", "company": "BHP", "year": 2016},
    {"filename": "BHP_17AR.pdf", "company": "BHP", "year": 2017},
    {"filename": "BHP_18AR.pdf", "company": "BHP", "year": 2018},
    {"filename": "BHP_19AR.pdf", "company": "BHP", "year": 2019},
    {"filename": "BHP_20AR.pdf", "company": "BHP", "year": 2020},
]

CONFIG = {
    "default_model": "gpt-4o-mini",
    "strong_model": "gpt-4o",
    "chunk_size": 1200,
    "chunk_overlap": 250,
    "max_turns": 25,
    "min_chunk_length": 100,
    "bm25_k1": 1.5,
    "bm25_b": 0.75,
}

# Enhanced stopwords for financial/governance documents
STOPWORDS = {
    "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "of",
    "with", "by", "from", "as", "is", "was", "are", "were", "been", "be", "have",
    "has", "had", "do", "does", "did", "will", "would", "could", "should", "may",
    "might", "must", "shall", "can", "this", "that", "these", "those", "it", "its",
    "we", "our", "they", "their", "you", "your", "he", "she", "him", "her", "his",
    "which", "who", "whom", "what", "where", "when", "why", "how", "all", "each",
    "every", "both", "few", "more", "most", "other", "some", "such", "no", "not",
    "only", "own", "same", "so", "than", "too", "very", "just", "also", "now",
    "bhp", "limited", "group", "company", "report", "annual", "page", "year"
}

# Metric vocabulary for corpus-aware query decomposition
# Maps abstract concepts to specific metrics found in BHP annual reports
METRIC_VOCABULARY = {
    "remuneration": {
        "metrics": ["fixed remuneration", "STI awarded", "LTI granted", "total remuneration",
                    "cash bonus", "equity award", "superannuation", "termination benefits"],
        "search_terms": ["remuneration table", "KMP remuneration", "executive pay",
                         "compensation", "salary", "incentive"],
        "typical_sections": ["Remuneration Report"],
    },
    "board_composition": {
        "metrics": ["number of directors", "independent directors", "female directors",
                    "director tenure", "board meetings attended", "committee membership"],
        "search_terms": ["board composition", "director appointment", "board diversity",
                         "non-executive director", "board skills matrix"],
        "typical_sections": ["Directors Report", "Corporate Governance"],
    },
    "safety": {
        "metrics": ["TRIFR", "LTIFR", "fatalities", "recordable injuries",
                    "high potential incidents", "safety incidents"],
        "search_terms": ["safety performance", "injury frequency", "fatality",
                         "health and safety", "lost time injury"],
        "typical_sections": ["Sustainability", "Operations Review"],
    },
    "financial": {
        "metrics": ["revenue", "underlying EBITDA", "profit attributable", "dividends per share",
                    "ROIC", "net debt", "free cash flow", "capital expenditure"],
        "search_terms": ["financial performance", "profit", "earnings", "cash flow"],
        "typical_sections": ["Financial Statements", "Operations Review"],
    },
    "sustainability": {
        "metrics": ["greenhouse gas emissions", "CO2 equivalent", "water consumption",
                    "energy consumption", "rehabilitation hectares", "community investment"],
        "search_terms": ["environmental performance", "emissions", "climate", "carbon"],
        "typical_sections": ["Sustainability"],
    },
    "governance": {
        "metrics": ["shareholder resolutions", "proxy votes", "AGM attendance",
                    "related party transactions", "audit fees", "non-audit fees"],
        "search_terms": ["corporate governance", "shareholder", "AGM", "audit committee"],
        "typical_sections": ["Corporate Governance", "Directors Report"],
    },
}

# Patterns that indicate abstract/interpretive queries
ABSTRACT_QUERY_PATTERNS = [
    r"how did .+ change",
    r"how has .+ evolved",
    r"what was the .+ strategy",
    r"what was the .+ approach",
    r"describe the .+ trend",
    r"explain the .+ policy",
    r"what factors .+ influenced",
    r"compare .+ over time",
    r"analyse .+ performance",
    r"assess .+ effectiveness",
    r"evolution of",
    r"trajectory of",
    r"progression of",
]

# Patterns that indicate concrete/factual queries
CONCRETE_QUERY_PATTERNS = [
    r"what was .+ in \d{4}",
    r"how much .+ in \d{4}",
    r"how many .+ in \d{4}",
    r"list .+ in \d{4}",
    r"total .+ for \d{4}",
    r"\$[\d,]+",
    r"\d+%",
    r"who was",
    r"who were",
    r"name of",
]


class PDFSource(BaseModel):
    filename: str
    company: str
    year: int
    document_type: str = "Annual Report"
    sha256_hash: str
    total_pages: int
    file_path: str

class DocumentChunk(BaseModel):
    chunk_id: str
    content: str
    company: str
    year: int
    page: int
    section: str = "General"
    source_file: str

class ClarifyingQuestions(BaseModel):
    questions: list[str]
    refined_query: str
    identified_companies: list[str]
    identified_years: list[int]
    focus_areas: list[str]
    # Query decomposition fields
    query_type: Literal["concrete", "quantifiable_abstract", "qualitative_abstract"] = "concrete"
    sub_queries: list[str] = []  # Metric-seeking sub-queries for quantifiable_abstract
    target_metrics: list[str] = []  # Expected metrics (e.g., "gender percentage", "dollar amount")

class AnalystFinding(BaseModel):
    finding: str
    evidence: str
    chunk_id: str
    page: int
    confidence: str = "high"
    category: str

class AnalystReport(BaseModel):
    analyst_name: str
    findings: list[AnalystFinding]
    summary: str
    red_flags: list[str] = []

class ReportData(BaseModel):
    short_summary: str
    markdown_report: str
    claims_made: list[str]
    follow_up_questions: list[str]

class ClaimVerification(BaseModel):
    claim: str
    status: str
    source_chunk_id: Optional[str] = None
    source_text: Optional[str] = None
    page: Optional[int] = None
    reason: Optional[str] = None

class VerificationResult(BaseModel):
    verified: bool
    total_claims: int
    verified_count: int
    claims: list[ClaimVerification]
    hallucinations: list[str] = []
    unsupported: list[str] = []

PDF_SOURCES = {}
ALL_CHUNKS = {}

def compute_sha256(file_path):
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            sha256_hash.update(chunk)
    return sha256_hash.hexdigest()

def detect_section(text: str) -> str:
    """Enhanced section detection with comprehensive keyword matching."""
    text_lower = text.lower()

    # Define section patterns with weighted keywords
    section_patterns = {
        "Remuneration Report": [
            "remuneration", "compensation", "kmp", "key management personnel",
            "executive pay", "salary", "bonus", "incentive", "long-term incentive",
            "short-term incentive", "lti", "sti", "equity award", "share-based",
            "performance right", "vesting", "clawback", "fixed remuneration"
        ],
        "Directors Report": [
            "board of directors", "director's report", "non-executive director",
            "chairman", "board composition", "board meeting", "director appointment",
            "director resignation", "board committee", "nomination committee"
        ],
        "Corporate Governance": [
            "corporate governance", "governance framework", "governance statement",
            "asx corporate governance", "governance principles", "board charter",
            "code of conduct", "ethics", "risk committee", "audit committee"
        ],
        "Financial Statements": [
            "consolidated statement", "balance sheet", "income statement",
            "cash flow statement", "statement of financial position",
            "profit and loss", "comprehensive income", "financial performance",
            "aasb", "ifrs", "accounting policy"
        ],
        "Risk Management": [
            "risk management", "risk factor", "principal risk", "operational risk",
            "financial risk", "market risk", "credit risk", "liquidity risk",
            "climate risk", "safety risk", "risk appetite", "risk assessment"
        ],
        "Related Party Disclosures": [
            "related party", "related parties", "key management", "transaction with",
            "director interests", "loan to director", "associate", "joint venture"
        ],
        "Sustainability": [
            "sustainability", "sustainable", "environmental", "social responsibility",
            "climate change", "carbon", "emissions", "greenhouse", "community",
            "indigenous", "safety performance", "health and safety", "fatality"
        ],
        "Operations Review": [
            "operations review", "operational review", "production", "petroleum",
            "minerals", "copper", "iron ore", "coal", "nickel", "potash",
            "exploration", "development", "capital expenditure", "capex"
        ],
    }

    scores = {}
    for section, keywords in section_patterns.items():
        score = sum(1 for kw in keywords if kw in text_lower)
        # Boost for exact phrase matches
        score += sum(2 for kw in keywords if len(kw.split()) > 1 and kw in text_lower)
        if score > 0:
            scores[section] = score

    if scores:
        return max(scores, key=scores.get)
    return "General"


def tokenize(text: str) -> List[str]:
    """Tokenize text, removing stopwords and short tokens."""
    # Convert to lowercase and extract alphanumeric tokens
    tokens = re.findall(r'\b[a-z0-9]+\b', text.lower())
    # Filter stopwords and short tokens
    return [t for t in tokens if t not in STOPWORDS and len(t) > 2]


def compute_idf(corpus_chunks: Dict[str, 'DocumentChunk']) -> Dict[str, float]:
    """Compute inverse document frequency for all terms."""
    doc_count = len(corpus_chunks)
    if doc_count == 0:
        return {}

    # Count documents containing each term
    doc_freq = Counter()
    for chunk in corpus_chunks.values():
        unique_terms = set(tokenize(chunk.content))
        doc_freq.update(unique_terms)

    # Calculate IDF with smoothing
    idf = {}
    for term, freq in doc_freq.items():
        idf[term] = math.log((doc_count - freq + 0.5) / (freq + 0.5) + 1)

    return idf


# Global IDF cache
IDF_SCORES = {}

def find_sentence_boundary(text: str, position: int, direction: str = "backward") -> int:
    """Find the nearest sentence boundary (. ! ? followed by space or newline)."""
    sentence_endings = re.compile(r'[.!?][\s\n]')

    if direction == "backward":
        # Search backward from position
        search_text = text[:position]
        matches = list(sentence_endings.finditer(search_text))
        if matches:
            # Return position after the sentence ending
            return matches[-1].end()
        return 0
    else:
        # Search forward from position
        search_text = text[position:]
        match = sentence_endings.search(search_text)
        if match:
            return position + match.end()
        return len(text)


def clean_text(text: str) -> str:
    """Clean extracted PDF text while preserving structure."""
    # Replace multiple whitespace with single space
    text = re.sub(r'[ \t]+', ' ', text)
    # Replace multiple newlines with double newline (preserve paragraphs)
    text = re.sub(r'\n{3,}', '\n\n', text)
    # Remove page headers/footers patterns (common in annual reports)
    text = re.sub(r'^\d+\s*$', '', text, flags=re.MULTILINE)
    text = re.sub(r'^BHP\s+Annual\s+Report\s+\d{4}\s*$', '', text, flags=re.MULTILINE | re.IGNORECASE)
    return text.strip()


def extract_pdf_chunks(pdf_path: Path, company: str, year: int) -> Tuple[PDFSource, List['DocumentChunk']]:
    """Extract text chunks from PDF with improved sentence boundary detection."""
    try:
        doc = fitz.open(pdf_path)
    except Exception as e:
        print(f"Error opening PDF {pdf_path}: {e}")
        return None, []

    source = PDFSource(
        filename=pdf_path.name, company=company, year=year,
        sha256_hash=compute_sha256(pdf_path),
        total_pages=len(doc), file_path=str(pdf_path)
    )

    chunks = []
    chunk_counter = 0
    chunk_size = CONFIG["chunk_size"]
    chunk_overlap = CONFIG["chunk_overlap"]
    min_length = CONFIG["min_chunk_length"]

    for page_num in range(len(doc)):
        try:
            text = doc[page_num].get_text()
        except Exception as e:
            print(f"Error extracting text from page {page_num + 1}: {e}")
            continue

        text = clean_text(text)
        if not text or len(text) < min_length:
            continue

        start = 0
        while start < len(text):
            # Calculate tentative end position
            tentative_end = start + chunk_size

            if tentative_end >= len(text):
                # Last chunk - take the rest
                chunk_text = text[start:].strip()
            else:
                # Find sentence boundary near the end
                # Look for boundary in the last 30% of the chunk
                search_start = start + int(chunk_size * 0.7)
                boundary = find_sentence_boundary(text[:tentative_end], tentative_end, "backward")

                if boundary > search_start:
                    chunk_text = text[start:boundary].strip()
                    tentative_end = boundary
                else:
                    # No good sentence boundary, try paragraph break
                    last_para = text[start:tentative_end].rfind('\n\n')
                    if last_para > chunk_size // 2:
                        chunk_text = text[start:start + last_para].strip()
                        tentative_end = start + last_para
                    else:
                        # Fall back to word boundary
                        last_space = text[start:tentative_end].rfind(' ')
                        if last_space > chunk_size // 2:
                            chunk_text = text[start:start + last_space].strip()
                            tentative_end = start + last_space
                        else:
                            chunk_text = text[start:tentative_end].strip()

            if chunk_text and len(chunk_text) >= min_length:
                chunk_id = f"{company.lower()}_{year}_p{page_num + 1:03d}_c{chunk_counter:03d}"
                chunks.append(DocumentChunk(
                    chunk_id=chunk_id,
                    content=chunk_text,
                    company=company,
                    year=year,
                    page=page_num + 1,
                    section=detect_section(chunk_text),
                    source_file=str(pdf_path)
                ))
                chunk_counter += 1

            # Move start with overlap, but ensure progress
            new_start = tentative_end - chunk_overlap
            if new_start <= start:
                new_start = start + min_length  # Ensure forward progress
            start = new_start

    doc.close()
    return source, chunks

def extract_all_pdfs():
    """Extract and index all PDF files with IDF computation."""
    global PDF_SOURCES, ALL_CHUNKS, IDF_SCORES
    PDF_SOURCES = {}
    ALL_CHUNKS = {}

    for pdf in PDF_FILES:
        path = ASSETS_DIR / pdf["filename"]
        if not path.exists():
            print(f"   Warning: {pdf['filename']} not found")
            continue
        print(f"   Processing {pdf['filename']}...", end=" ", flush=True)
        source, chunks = extract_pdf_chunks(path, pdf["company"], pdf["year"])
        if source is None:
            print("Failed")
            continue
        PDF_SOURCES[pdf["filename"]] = source
        for c in chunks:
            ALL_CHUNKS[c.chunk_id] = c
        print(f"{len(chunks)} chunks")

    # Compute IDF scores for the entire corpus
    print("   Computing IDF scores...", end=" ", flush=True)
    IDF_SCORES = compute_idf(ALL_CHUNKS)
    print(f"{len(IDF_SCORES)} terms indexed")


def compute_bm25_score(query_tokens: List[str], chunk: 'DocumentChunk', avg_doc_len: float) -> float:
    """Compute BM25 score for a chunk given query tokens."""
    k1 = CONFIG["bm25_k1"]
    b = CONFIG["bm25_b"]

    chunk_tokens = tokenize(chunk.content)
    doc_len = len(chunk_tokens)
    term_freq = Counter(chunk_tokens)

    score = 0.0
    for term in query_tokens:
        if term not in term_freq:
            continue

        tf = term_freq[term]
        idf = IDF_SCORES.get(term, 0)

        # BM25 formula
        numerator = tf * (k1 + 1)
        denominator = tf + k1 * (1 - b + b * (doc_len / avg_doc_len))
        score += idf * (numerator / denominator)

    return score


def compute_phrase_bonus(query: str, content: str) -> float:
    """Compute bonus for phrase matches (multi-word sequences)."""
    query_lower = query.lower()
    content_lower = content.lower()

    bonus = 0.0

    # Extract 2-word and 3-word phrases from query
    words = query_lower.split()
    for n in [2, 3]:
        for i in range(len(words) - n + 1):
            phrase = ' '.join(words[i:i + n])
            if phrase in content_lower:
                bonus += n * 2  # Higher bonus for longer phrase matches

    return bonus


def _detect_chunk_characteristics(content: str) -> Dict[str, bool]:
    """
    Detect characteristics of a chunk that suggest it needs context.

    Returns flags indicating:
    - has_table: Likely contains tabular data
    - has_figures: Contains monetary/percentage figures
    - has_cross_ref: References other parts of the document
    - needs_context: Composite flag suggesting context retrieval would help
    """
    content_lower = content.lower()

    # Table detection heuristics
    table_indicators = [
        # Multiple dollar amounts in close proximity (likely a table)
        len(re.findall(r'\$[\d,]+(?:\.\d+)?(?:\s*(?:m|million|k|thousand|bn|billion))?', content_lower)) >= 3,
        # Multiple percentage values
        len(re.findall(r'\d+(?:\.\d+)?\s*%', content)) >= 3,
        # Column-like patterns (multiple values separated by whitespace on same conceptual row)
        bool(re.search(r'(?:\d[\d,]*\s+){3,}', content)),
        # Common table headers in financial reports
        any(header in content_lower for header in [
            'total', 'subtotal', 'fixed remuneration', 'cash bonus',
            'sti', 'lti', 'equity', 'base salary', 'superannuation'
        ]) and len(re.findall(r'\$[\d,]+', content)) >= 2,
        # Year columns pattern (e.g., "2019 2020 2021")
        bool(re.search(r'20\d{2}\s+20\d{2}', content)),
    ]
    has_table = sum(table_indicators) >= 2

    # Figure detection
    has_figures = bool(re.search(
        r'\$[\d,]+(?:\.\d+)?(?:\s*(?:m|million|k|thousand|bn|billion))?',
        content_lower
    ))

    # Cross-reference detection
    cross_ref_patterns = [
        r'\bsee\s+note\s+\d+',
        r'\brefer\s+to\s+(?:page|section|note)',
        r'\bnote\s+\d+\b',
        r'\bpage\s+\d+\b',
        r'\bsection\s+\d+',
        r'\bas\s+(?:detailed|described|outlined)\s+(?:in|on)',
    ]
    has_cross_ref = any(re.search(p, content_lower) for p in cross_ref_patterns)

    # Composite: suggest context if table without explanation, or has cross-refs
    # Tables typically need narrative; cross-refs need the referenced content
    needs_context = has_table or has_cross_ref

    return {
        'has_table': has_table,
        'has_figures': has_figures,
        'has_cross_ref': has_cross_ref,
        'needs_context': needs_context,
    }


def _format_context_hint(characteristics: Dict[str, bool]) -> str:
    """Format a context hint string for search results."""
    hints = []
    if characteristics['has_table']:
        hints.append("📊 TABLE")
    if characteristics['has_cross_ref']:
        hints.append("🔗 CROSS-REF")
    if characteristics['has_figures'] and not characteristics['has_table']:
        hints.append("💰 FIGURES")

    if hints:
        return f"**Context Hint:** {' | '.join(hints)} → Use `get_chunk_with_context` for full picture"
    return ""


def _search_annual_reports(
    query: str,
    company: str = "BHP",
    years: Optional[List[int]] = None,
    section: Optional[str] = None,
    max_results: int = 8
) -> str:
    """
    Search annual reports using BM25 ranking with phrase matching.

    Args:
        query: Search query string
        company: Company name to search (default: BHP)
        years: List of years to search, or None for all years
        section: Optional section filter
        max_results: Maximum number of results to return
    """
    if not ALL_CHUNKS:
        return "ERROR: No documents loaded. Please ensure PDFs are in the assets folder."

    query_tokens = tokenize(query)
    if not query_tokens:
        return f"No valid search terms in query: '{query}'. Try using more specific keywords."

    # Calculate average document length for BM25
    all_lengths = [len(tokenize(c.content)) for c in ALL_CHUNKS.values()]
    avg_doc_len = sum(all_lengths) / len(all_lengths) if all_lengths else 100

    results = []
    for chunk_id, chunk in ALL_CHUNKS.items():
        # Apply filters
        if chunk.company.upper() != company.upper():
            continue
        if years and chunk.year not in years:
            continue
        if section and section.lower() not in chunk.section.lower():
            continue

        # Compute BM25 score
        bm25_score = compute_bm25_score(query_tokens, chunk, avg_doc_len)

        if bm25_score > 0:
            # Add phrase match bonus
            phrase_bonus = compute_phrase_bonus(query, chunk.content)

            # Section relevance boost
            section_boost = 1.0
            query_lower = query.lower()
            if "remuneration" in query_lower and "remuneration" in chunk.section.lower():
                section_boost = 1.5
            elif "governance" in query_lower and "governance" in chunk.section.lower():
                section_boost = 1.5
            elif "risk" in query_lower and "risk" in chunk.section.lower():
                section_boost = 1.5

            total_score = (bm25_score + phrase_bonus) * section_boost
            results.append((total_score, chunk))

    results.sort(key=lambda x: x[0], reverse=True)

    if not results:
        year_info = f" for years {years}" if years else ""
        section_info = f" in section '{section}'" if section else ""
        return f"No results found for '{query}'{year_info}{section_info}. Try broadening your search terms."

    # Format output
    out = [f"Found {len(results)} matching chunks. Showing top {min(max_results, len(results))} results:\n"]

    for rank, (score, c) in enumerate(results[:max_results], 1):
        content = c.content[:700] + "..." if len(c.content) > 700 else c.content

        # Detect chunk characteristics and generate context hint
        characteristics = _detect_chunk_characteristics(c.content)
        context_hint = _format_context_hint(characteristics)

        result_block = (
            f"---\n"
            f"**Result {rank}** (Score: {score:.2f})\n"
            f"**[{c.company} {c.year} Annual Report, Page {c.page}]**\n"
            f"**Section:** {c.section}\n"
        )
        if context_hint:
            result_block += f"{context_hint}\n"
        result_block += f"\n{content}\n\n**Citation:** [Chunk ID: {c.chunk_id}]\n"

        out.append(result_block)

    return "\n".join(out)

@function_tool
def search_annual_reports(
    query: str,
    company: str = "BHP",
    years: List[int] = None,
    section: str = None,
    max_results: int = 8
) -> str:
    """
    Search annual reports for governance-related content using semantic search.

    Args:
        query: Natural language search query (e.g., "CEO remuneration packages")
        company: Company name to search (default: "BHP")
        years: List of years to search (e.g., [2019, 2020]). If None, searches all available years.
        section: Optional section filter (e.g., "Remuneration Report", "Corporate Governance")
        max_results: Maximum results to return (default: 8)

    Returns:
        Formatted search results with citations and chunk IDs for verification.
    """
    return _search_annual_reports(query, company, years, section, max_results)

def _get_chunk_by_id(chunk_id):
    if chunk_id not in ALL_CHUNKS:
        return f"ERROR: Chunk ID '{chunk_id}' not found."
    c = ALL_CHUNKS[chunk_id]
    return f"**Chunk ID:** {c.chunk_id}\n**Source:** {c.company} {c.year} AR, Page {c.page}\n**Section:** {c.section}\n\n**Content:**\n{c.content}"


def _parse_chunk_number(chunk_id: str) -> int:
    """Extract the chunk number from a chunk_id like 'bhp_2019_p152_c033'."""
    try:
        return int(chunk_id.split('_')[-1][1:])
    except (ValueError, IndexError):
        return -1


def _get_chunk_with_context(
    chunk_id: str,
    window: int = 2,
    same_section_only: bool = True,
    include_cross_references: bool = True
) -> List[DocumentChunk]:
    """
    Retrieve a chunk plus its surrounding context from the document neighbourhood.

    Args:
        chunk_id: The target chunk ID
        window: Number of chunks before/after to include
        same_section_only: If True, only include chunks from the same section
        include_cross_references: If True, also fetch chunks referenced by Note/Table mentions

    Returns:
        List of DocumentChunk objects ordered by position
    """
    target = ALL_CHUNKS.get(chunk_id)
    if not target:
        return []

    target_num = _parse_chunk_number(chunk_id)

    # Get candidate chunks from same document, same page ±1
    candidates = [
        c for c in ALL_CHUNKS.values()
        if c.company == target.company
        and c.year == target.year
        and abs(c.page - target.page) <= 1
    ]

    # Optionally filter to same section
    if same_section_only:
        candidates = [c for c in candidates if c.section == target.section]

    # Sort by chunk number proximity to target
    candidates.sort(key=lambda c: abs(_parse_chunk_number(c.chunk_id) - target_num))

    # Take the window of nearest chunks
    context_chunks = candidates[:window * 2 + 1]

    # Look for cross-references (Note X, Table X, Page X)
    if include_cross_references:
        cross_ref_chunks = _find_cross_referenced_chunks(target)
        for ref_chunk in cross_ref_chunks:
            if ref_chunk not in context_chunks:
                context_chunks.append(ref_chunk)

    # Sort final results by page then chunk number for logical reading order
    context_chunks.sort(key=lambda c: (c.page, _parse_chunk_number(c.chunk_id)))

    return context_chunks


def _find_cross_referenced_chunks(chunk: DocumentChunk) -> List[DocumentChunk]:
    """
    Find chunks that are referenced by Note/Table/Section mentions in the content.

    Looks for patterns like "Note 23", "Table 5", "see page 150" and attempts
    to find the corresponding chunks in the same document.
    """
    cross_refs = []
    content_lower = chunk.content.lower()

    # Pattern: "Note X" or "note X" - look for chunks containing that note
    note_matches = re.findall(r'\bnotes?\s+(\d+)\b', content_lower)
    for note_num in note_matches[:3]:  # Limit to first 3 to avoid over-fetching
        # Search for chunks that contain "Note {num}" as a heading/definition
        note_pattern = f"note {note_num}"
        for c in ALL_CHUNKS.values():
            if (c.company == chunk.company
                and c.year == chunk.year
                and c.chunk_id != chunk.chunk_id
                and note_pattern in c.content.lower()[:200]):  # Check start of chunk
                cross_refs.append(c)
                break  # Only get first match per note

    # Pattern: "page X" references
    page_matches = re.findall(r'\bpage\s+(\d+)\b', content_lower)
    for page_num in page_matches[:2]:  # Limit to first 2
        try:
            page_int = int(page_num)
            # Get first chunk from that page
            for c in ALL_CHUNKS.values():
                if (c.company == chunk.company
                    and c.year == chunk.year
                    and c.page == page_int):
                    cross_refs.append(c)
                    break
        except ValueError:
            continue

    return cross_refs


@function_tool
def get_chunk_by_id(chunk_id: str) -> str:
    """Retrieve a chunk by ID."""
    return _get_chunk_by_id(chunk_id)


@function_tool
def get_chunk_with_context(
    chunk_id: str,
    window: int = 2,
    same_section_only: bool = True
) -> str:
    """
    Retrieve a chunk along with its surrounding document context.

    Use this when you need to understand the full context of a finding,
    especially when a chunk contains a table that needs narrative explanation,
    or narrative that references nearby figures.

    Args:
        chunk_id: The target chunk ID (e.g., "bhp_2019_p152_c033")
        window: Number of chunks before/after to include (default: 2)
        same_section_only: If True, only include chunks from same section (default: True)

    Returns:
        The target chunk plus surrounding context chunks in reading order.
    """
    context_chunks = _get_chunk_with_context(chunk_id, window, same_section_only)

    if not context_chunks:
        return f"ERROR: Chunk ID '{chunk_id}' not found."

    # Find the target chunk to highlight it
    target = ALL_CHUNKS.get(chunk_id)

    out = [f"## Document Context for {chunk_id}\n"]
    out.append(f"**Document:** {target.company} {target.year} Annual Report")
    out.append(f"**Section:** {target.section}")
    out.append(f"**Showing {len(context_chunks)} chunks in context**\n")
    out.append("---\n")

    for c in context_chunks:
        is_target = c.chunk_id == chunk_id
        marker = ">>> TARGET >>>" if is_target else ""

        out.append(f"**[Page {c.page}] {c.chunk_id}** {marker}")
        if c.section != target.section:
            out.append(f"*(Section: {c.section})*")
        out.append(f"\n{c.content}\n")
        out.append("---\n")

    return "\n".join(out)

@function_tool
def list_available_years(company: str = "BHP") -> str:
    """List available years."""
    years = set(c.year for c in ALL_CHUNKS.values() if c.company.upper() == company.upper())
    return f"Available: {sorted(years)}" if years else f"No data for {company}"

@function_tool
def get_section_summary(
    section: str,
    company: str = "BHP",
    year: int = None,
    max_chunks: int = 5
) -> str:
    """
    Get summary of chunks from a specific section of annual reports.

    Args:
        section: Section name (e.g., "Remuneration Report", "Corporate Governance")
        company: Company name (default: "BHP")
        year: Specific year or None for all years
        max_chunks: Maximum chunks to return
    """
    matching = [
        c for c in ALL_CHUNKS.values()
        if c.company.upper() == company.upper()
        and section.lower() in c.section.lower()
        and (year is None or c.year == year)
    ]

    if not matching:
        available_sections = set(c.section for c in ALL_CHUNKS.values())
        return f"No '{section}' chunks found. Available sections: {sorted(available_sections)}"

    # Sort by year (descending) then page
    matching.sort(key=lambda c: (-c.year, c.page))

    out = f"Found {len(matching)} chunks in '{section}'. Showing {min(max_chunks, len(matching))}:\n"

    for c in matching[:max_chunks]:
        content_preview = c.content[:400] + "..." if len(c.content) > 400 else c.content
        out += f"\n---\n**[{c.company} {c.year} AR, Page {c.page}]**\n{content_preview}\n[Chunk ID: {c.chunk_id}]\n"

    return out


@function_tool
def compare_years(
    topic: str,
    company: str = "BHP",
    year1: int = 2019,
    year2: int = 2020,
    max_results_per_year: int = 3
) -> str:
    """
    Compare information about a topic across two different years.

    Args:
        topic: Topic to compare (e.g., "CEO remuneration", "board composition")
        company: Company name (default: "BHP")
        year1: First year to compare
        year2: Second year to compare
        max_results_per_year: Maximum results per year
    """
    results_y1 = _search_annual_reports(topic, company, [year1], None, max_results_per_year)
    results_y2 = _search_annual_reports(topic, company, [year2], None, max_results_per_year)

    return f"""## Year-over-Year Comparison: {topic}

### {year1} Results:
{results_y1}

### {year2} Results:
{results_y2}

---
Use the chunk IDs above to verify specific claims and extract exact figures for comparison.
"""


@function_tool
def get_available_sections(company: str = "BHP", year: int = None) -> str:
    """
    List all available sections in the document corpus with chunk counts.

    Args:
        company: Company name (default: "BHP")
        year: Specific year or None for all years
    """
    section_counts = {}
    for c in ALL_CHUNKS.values():
        if c.company.upper() != company.upper():
            continue
        if year and c.year != year:
            continue
        key = (c.section, c.year)
        section_counts[key] = section_counts.get(key, 0) + 1

    if not section_counts:
        return f"No documents found for {company}" + (f" in {year}" if year else "")

    # Group by section
    sections = {}
    for (section, yr), count in section_counts.items():
        if section not in sections:
            sections[section] = {}
        sections[section][yr] = count

    out = f"## Available Sections for {company}\n\n"
    for section in sorted(sections.keys()):
        years_info = ", ".join([f"{y}: {c} chunks" for y, c in sorted(sections[section].items())])
        out += f"- **{section}**: {years_info}\n"

    return out

CLARIFIER_INSTRUCTIONS = """You are a governance research query clarification and decomposition specialist.

Your task is to analyse user queries about corporate governance, classify them, and prepare them
for high-accuracy retrieval. Your goal is to convert abstract questions into metric-anchored
searches that will produce verifiable findings.

AVAILABLE DATA:
- Company: BHP (mining company)
- Years: 2016, 2017, 2018, 2019, 2020 Annual Reports
- Sections: Remuneration Report, Directors Report, Corporate Governance, Financial Statements,
  Risk Management, Related Party Disclosures, Sustainability, Operations Review

AVAILABLE METRICS BY TOPIC:
- Remuneration: fixed remuneration, STI awarded, LTI granted, total remuneration, cash bonus,
  equity award, superannuation, termination benefits
- Board: number of directors, independent directors, female directors, director tenure,
  board meetings attended, committee membership, board skills matrix
- Safety: TRIFR, LTIFR, fatalities, recordable injuries, high potential incidents
- Financial: revenue, underlying EBITDA, profit attributable, dividends per share, ROIC,
  net debt, free cash flow, capital expenditure
- Sustainability: greenhouse gas emissions, CO2 equivalent, water consumption, energy consumption
- Governance: shareholder resolutions, proxy votes, AGM attendance, related party transactions

STEP 1: CLASSIFY THE QUERY TYPE

Determine query_type based on these criteria:

"concrete" - Query seeks specific facts with explicit targets:
  - Mentions specific years, dollar amounts, percentages, or named individuals
  - Examples: "What was CEO pay in 2019?", "How many fatalities in 2020?", "List board members in 2018"

"quantifiable_abstract" - Query is abstract BUT can be answered with metrics:
  - Asks about change, evolution, trends, comparisons over time
  - Examples: "How did board diversity change?", "What was the remuneration trend?",
    "Compare safety performance across years"
  - These MUST be decomposed into metric-seeking sub-queries

"qualitative_abstract" - Query is abstract and requires narrative/policy descriptions:
  - Asks about rationale, philosophy, approach, stated reasons
  - Examples: "What was the board's rationale for the pay increase?",
    "How did management explain the safety incidents?", "What is BHP's governance philosophy?"
  - These cannot be fully answered with metrics alone

STEP 2: FOR quantifiable_abstract QUERIES, GENERATE SUB-QUERIES

Convert the abstract question into 3-5 concrete, metric-seeking sub-queries:

Example: "How did board diversity change from 2017 to 2020?"
sub_queries:
  - "board composition female directors 2017"
  - "board composition female directors 2020"
  - "director appointments gender 2017 2018 2019 2020"
  - "board diversity policy commitments"
target_metrics: ["female director count", "female director percentage", "diversity targets"]

Example: "What was the trend in executive compensation?"
sub_queries:
  - "CEO total remuneration 2016 2017 2018 2019 2020"
  - "KMP fixed remuneration comparison"
  - "STI LTI awards trend"
  - "executive pay ratio"
target_metrics: ["total remuneration dollars", "STI percentage", "LTI percentage", "year-on-year change"]

STEP 3: OUTPUT ALL FIELDS

- questions: 2-3 clarifying questions that could further refine the research
- refined_query: A clear, keyword-rich version of the query (for concrete) or the synthesis goal (for abstract)
- identified_companies: Always ["BHP"] for this dataset
- identified_years: List of relevant years (extract from query or default [2019, 2020])
- focus_areas: List of relevant section types to focus on
- query_type: One of "concrete", "quantifiable_abstract", "qualitative_abstract"
- sub_queries: For quantifiable_abstract, list 3-5 metric-seeking search queries. Empty list otherwise.
- target_metrics: For quantifiable_abstract, list the specific metrics expected. Empty list otherwise.

IMPORTANT: For quantifiable_abstract queries, the sub_queries should use terminology from the
AVAILABLE METRICS list above, as these terms appear in the actual documents.
"""

clarifier_agent = Agent(
    name="ClarifierAgent",
    instructions=CLARIFIER_INSTRUCTIONS,
    model=CONFIG["default_model"],
    output_type=ClarifyingQuestions,
)

ANALYST_INSTRUCTIONS = """You are a governance analyst for BHP annual reports.

STRICT RULES - FOLLOW EXACTLY:
1. Do ONE search using search_annual_reports with keywords from the query
2. For any chunk containing a table or financial figures, use get_chunk_with_context
   to retrieve the surrounding narrative that explains the numbers
3. Extract 3-5 findings from the results
4. Return your AnalystReport immediately

WHEN TO USE get_chunk_with_context:
- When a search result contains a table but lacks explanation of what the figures mean
- When a result mentions "see Note X" or "refer to page Y"
- When you need to understand year-on-year changes that may span multiple chunks
- When a result contains figures like "$12.4m" but doesn't explain what it's for

DO NOT:
- Search more than once
- Keep searching for "better" results
- Loop or retry
- Call get_chunk_with_context more than twice per query

After your first search, optionally get context for 1-2 key chunks, then compile
whatever findings you have and return them.
If no results found, return empty findings with summary "No relevant content found".
"""

remuneration_analyst = Agent(
    name="GovernanceAnalyst",
    instructions=ANALYST_INSTRUCTIONS,
    tools=[
        search_annual_reports,
        get_chunk_by_id,
        get_chunk_with_context,
        list_available_years,
        get_section_summary,
        compare_years,
        get_available_sections
    ],
    model=CONFIG["default_model"],
    output_type=AnalystReport,
)

WRITER_INSTRUCTIONS = """You are a professional governance report writer.

Your task is to synthesise analyst findings into a clear, well-structured report.

ABSOLUTE RULES:
1. Use ONLY the findings provided - NO external knowledge or assumptions
2. EVERY factual claim MUST include a citation in format [Chunk ID: xxx]
3. If a finding lacks a chunk ID, DO NOT include it in the report
4. Distinguish clearly between facts (from documents) and analysis (your interpretation)

REPORT STRUCTURE:
## Executive Summary
Brief 2-3 sentence overview of key findings

## Key Findings
Bullet points of most important discoveries with citations

## Detailed Analysis
In-depth discussion organised by theme, all claims cited

## Red Flags & Concerns
Any governance issues, unusual patterns, or areas requiring attention

## Recommendations
Suggested follow-up research or actions

## Sources
List all Chunk IDs used in the report

CITATION FORMAT:
- Inline citations: "The CEO received $X in total compensation [Chunk ID: bhp_2019_p152_c001]"
- Every paragraph with factual claims should have at least one citation

RED FLAGS RULES:
- Only flag issues explicitly stated or mathematically derived from source documents
- Do NOT speculate about motivations, dissatisfaction, or sentiment
- Do NOT use phrases like 'may signal', 'may raise concerns', 'could indicate', 'potentially'
- State only observable facts: e.g., '24% decrease in total remuneration' NOT 'may signal dissatisfaction'
- If no red flags are explicitly supported by evidence, state 'No red flags identified in source documents'

FORBIDDEN PHRASES:
- "may signal"
- "may raise concerns"
- "could indicate"
- "potentially suggests"
- "might reflect"
- "possibly due to"
- Any speculation about intent, motivation, or sentiment not directly quoted from source

SENSITIVE CLAIM MODE:
For claims about fatalities, incidents, safety outcomes, legal matters, or regulatory findings:
- Use EXACT language from source for key characterisations
- Do NOT paraphrase cause, preventability, fault, or responsibility
- If source says "unable to determine cause", do NOT rephrase as "unpreventable" or "unavoidable"
- When uncertain about sensitive characterisations, quote directly with attribution: 'The report states "..."'
- This applies to: deaths, injuries, TRIFR/safety metrics, regulatory penalties, legal findings, compliance violations
"""

writer_agent = Agent(
    name="WriterAgent",
    instructions=WRITER_INSTRUCTIONS,
    model=CONFIG["default_model"],
    output_type=ReportData,
)

VERIFIER_INSTRUCTIONS = """You are a forensic verification specialist ensuring report accuracy.

Your task is to verify EVERY claim in the report against source documents.

VERIFICATION PROCESS:
For each claim in the report:
1. Check if it has a citation [Chunk ID: xxx]
2. Retrieve the chunk using get_chunk_by_id
3. Verify the claim accurately reflects the source content
4. Assign verification status

VERIFICATION STATUSES:
- VERIFIED: Claim has citation AND source text supports it
- UNSUPPORTED: Claim has citation BUT source doesn't fully support it
- HALLUCINATION: Claim has NO citation OR chunk doesn't exist OR claim contradicts source

STRICT STANDARDS:
- Numbers must match exactly (or be clearly indicated as approximate)
- Quotes must be accurate
- Context must not be misleading
- Inferences must be reasonable based on source

OUTPUT:
- List each claim with its verification status
- Provide the source text for verified claims
- Explain why claims are unsupported or hallucinated
- Overall verified status: TRUE only if >80% of claims verified
"""

verifier_agent = Agent(
    name="VerifierAgent",
    instructions=VERIFIER_INSTRUCTIONS,
    tools=[get_chunk_by_id, get_chunk_with_context],
    model=CONFIG["strong_model"],
    output_type=VerificationResult,
)

def _run_sub_query_retrieval(
    sub_queries: List[str],
    years: List[int],
    max_results_per_query: int = 5
) -> Tuple[List[DocumentChunk], str]:
    """
    Run multiple sub-queries and collect unique chunks.

    Returns:
        Tuple of (deduplicated chunks, formatted results string)
    """
    all_chunks: Dict[str, DocumentChunk] = {}
    results_log = []

    for i, sub_query in enumerate(sub_queries, 1):
        results_log.append(f"\n**Sub-query {i}:** {sub_query}")

        # Run search for this sub-query
        query_tokens = tokenize(sub_query)
        if not query_tokens:
            results_log.append("   (No valid search terms)")
            continue

        # Calculate average doc length for BM25
        all_lengths = [len(tokenize(c.content)) for c in ALL_CHUNKS.values()]
        avg_doc_len = sum(all_lengths) / len(all_lengths) if all_lengths else 100

        # Score and rank chunks
        scored_results = []
        for chunk_id, chunk in ALL_CHUNKS.items():
            if years and chunk.year not in years:
                continue

            bm25_score = compute_bm25_score(query_tokens, chunk, avg_doc_len)
            if bm25_score > 0:
                phrase_bonus = compute_phrase_bonus(sub_query, chunk.content)
                total_score = bm25_score + phrase_bonus
                scored_results.append((total_score, chunk))

        scored_results.sort(key=lambda x: x[0], reverse=True)

        # Add top results to collection
        added_count = 0
        for score, chunk in scored_results[:max_results_per_query]:
            if chunk.chunk_id not in all_chunks:
                all_chunks[chunk.chunk_id] = chunk
                added_count += 1

        results_log.append(f"   Found {len(scored_results)} matches, added {added_count} new chunks")

    # Format the collected chunks for display
    formatted_chunks = []
    for chunk in sorted(all_chunks.values(), key=lambda c: (c.year, c.page)):
        characteristics = _detect_chunk_characteristics(chunk.content)
        context_hint = _format_context_hint(characteristics)

        chunk_text = chunk.content[:600] + "..." if len(chunk.content) > 600 else chunk.content
        formatted = (
            f"---\n"
            f"**[{chunk.company} {chunk.year} AR, Page {chunk.page}]** | Section: {chunk.section}\n"
        )
        if context_hint:
            formatted += f"{context_hint}\n"
        formatted += f"\n{chunk_text}\n\n**[Chunk ID: {chunk.chunk_id}]**\n"
        formatted_chunks.append(formatted)

    results_summary = "\n".join(results_log)
    chunks_output = "\n".join(formatted_chunks)

    return list(all_chunks.values()), f"{results_summary}\n\n## Retrieved Chunks ({len(all_chunks)} unique):\n{chunks_output}"


class GovernanceResearchManager:
    """Orchestrates the multi-agent research pipeline."""

    def __init__(self):
        self.max_turns = CONFIG["max_turns"]
        self.chunks_retrieved: List[str] = []
        self.errors: List[str] = []
        self.query_type: str = "concrete"
        self.confidence_level: str = "high"

    async def run(self, query: str):
        """
        Execute the research pipeline with comprehensive error handling.

        Yields status updates and finally returns the complete output dict.
        """
        trace_id = gen_trace_id()

        with trace("Governance Research", trace_id=trace_id):
            yield f"Trace: https://platform.openai.com/traces/{trace_id}"

            # Step 1: Query Clarification and Classification
            yield "\nStep 1: Classifying and decomposing query..."
            try:
                clarification_result = await Runner.run(
                    clarifier_agent,
                    f"Analyse this governance research query: {query}",
                    max_turns=5
                )
                clarification = clarification_result.final_output_as(ClarifyingQuestions)
                years = clarification.identified_years if clarification.identified_years else [2019, 2020]
                focus_areas = clarification.focus_areas if clarification.focus_areas else ["Remuneration Report"]
                self.query_type = clarification.query_type

                # Log the classification
                yield f"   Query type: {self.query_type}"
                yield f"   Years: {years}, Focus: {focus_areas}"

                if self.query_type == "quantifiable_abstract" and clarification.sub_queries:
                    yield f"   Decomposed into {len(clarification.sub_queries)} sub-queries:"
                    for sq in clarification.sub_queries:
                        yield f"      - {sq}"
                    if clarification.target_metrics:
                        yield f"   Target metrics: {', '.join(clarification.target_metrics)}"

                if self.query_type == "qualitative_abstract":
                    self.confidence_level = "medium"
                    yield "   ⚠ Qualitative query - answer will be based on narrative, confidence reduced"

            except Exception as e:
                self.errors.append(f"Clarification failed: {str(e)}")
                yield f"   Warning: Clarification failed, using defaults. Error: {str(e)[:100]}"
                years = [2019, 2020]
                focus_areas = ["Remuneration Report", "Corporate Governance"]
                clarification = ClarifyingQuestions(
                    questions=[],
                    refined_query=query,
                    identified_companies=["BHP"],
                    identified_years=years,
                    focus_areas=focus_areas,
                    query_type="concrete",
                    sub_queries=[],
                    target_metrics=[]
                )

            # Step 2: Document Analysis (with sub-query retrieval for abstract queries)
            yield "\nStep 2: Analysing documents..."

            # For quantifiable_abstract queries, run sub-queries first
            pre_fetched_context = ""
            if self.query_type == "quantifiable_abstract" and clarification.sub_queries:
                yield "   Running metric-seeking sub-queries..."
                pre_fetched_chunks, retrieval_log = _run_sub_query_retrieval(
                    clarification.sub_queries,
                    years,
                    max_results_per_query=5
                )
                for chunk in pre_fetched_chunks:
                    self.chunks_retrieved.append(chunk.chunk_id)

                yield f"   Pre-fetched {len(pre_fetched_chunks)} unique chunks from {len(clarification.sub_queries)} sub-queries"

                # Build context string for the analyst
                pre_fetched_context = f"""
## PRE-FETCHED EVIDENCE (from decomposed sub-queries)
The original abstract query has been decomposed into metric-seeking sub-queries.
Below are the chunks retrieved. Extract findings from these chunks.

{retrieval_log}

---
IMPORTANT: Base your findings ONLY on the chunks above. The goal is to answer the
original abstract question "{query}" using ONLY quantitative evidence from these chunks.
Target metrics to find: {', '.join(clarification.target_metrics) if clarification.target_metrics else 'specific numbers, percentages, dollar amounts'}
"""

            try:
                # Build analysis prompt based on query type
                if self.query_type == "quantifiable_abstract" and pre_fetched_context:
                    analysis_prompt = f"""Research Query: {query}
Query Type: QUANTIFIABLE ABSTRACT - Answer using metrics from pre-fetched chunks

{pre_fetched_context}

CRITICAL INSTRUCTIONS - FOLLOW EXACTLY:
1. DO NOT call any tools - all evidence is already provided above
2. Extract 3-5 findings from the pre-fetched chunks above
3. Every finding MUST cite a specific chunk ID (e.g., bhp_2019_p152_c001)
4. Include exact numbers (dollar amounts, percentages, counts)
5. Return your AnalystReport IMMEDIATELY after extracting findings

DO NOT make general statements without specific figures.
DO NOT call search_annual_reports or any other tool.
DO NOT call get_chunk_with_context - context is already provided.
The chunks above contain everything you need. Extract findings and return immediately."""

                elif self.query_type == "qualitative_abstract":
                    analysis_prompt = f"""Research Query: {query}
Query Type: QUALITATIVE ABSTRACT - Narrative/policy-based answer expected

Search BHP Annual Reports for the following:
- Years to focus on: {years}
- Relevant sections: {focus_areas}
- Refined query: {clarification.refined_query}

This is a qualitative query seeking narrative descriptions, rationale, or policy statements.
Find relevant passages that address the query. Include direct quotes where possible.
Mark confidence as "medium" for interpretive findings.
Ensure every finding has a valid Chunk ID citation."""

                else:  # concrete query
                    analysis_prompt = f"""Research Query: {query}
Query Type: CONCRETE - Specific factual answer expected

Search BHP Annual Reports for the following:
- Years to focus on: {years}
- Relevant sections: {focus_areas}
- Refined query: {clarification.refined_query}

Find specific evidence with exact figures, quotes, and page references.
Ensure every finding has a valid Chunk ID citation."""

                analysis_result = await Runner.run(
                    remuneration_analyst,
                    analysis_prompt,
                    max_turns=self.max_turns
                )
                analyst_report = analysis_result.final_output_as(AnalystReport)
                findings = analyst_report.findings

                # Validate findings have chunk IDs
                valid_findings = []
                for f in findings:
                    if f.chunk_id and f.chunk_id in ALL_CHUNKS:
                        # Adjust confidence for qualitative queries
                        if self.query_type == "qualitative_abstract":
                            f.confidence = "medium"
                        valid_findings.append(f)
                        self.chunks_retrieved.append(f.chunk_id)
                    else:
                        self.errors.append(f"Invalid chunk ID in finding: {f.chunk_id}")

                if not valid_findings:
                    yield "   Warning: No valid findings with verifiable sources found"
                    # Create placeholder finding
                    valid_findings = findings[:3] if findings else []

                yield f"   Done. Found {len(valid_findings)} verified findings (of {len(findings)} total)"

            except Exception as e:
                self.errors.append(f"Analysis failed: {str(e)}")
                yield f"   Error in analysis: {str(e)[:100]}"
                valid_findings = []
                analyst_report = AnalystReport(
                    analyst_name="GovernanceAnalyst",
                    findings=[],
                    summary="Analysis could not be completed due to an error.",
                    red_flags=["Analysis pipeline error - results may be incomplete"]
                )

            # Step 3: Report Writing
            yield "\nStep 3: Writing report..."
            try:
                if valid_findings:
                    findings_text = "\n\n".join([
                        f"**Finding {i+1}:** {f.finding}\n"
                        f"**Evidence:** {f.evidence}\n"
                        f"**Source:** [Chunk ID: {f.chunk_id}] (Page {f.page})\n"
                        f"**Category:** {f.category}\n"
                        f"**Confidence:** {f.confidence}"
                        for i, f in enumerate(valid_findings)
                    ])
                else:
                    findings_text = "No verified findings available. Report based on general search results."

                # Add query type context for the writer
                query_type_guidance = ""
                if self.query_type == "quantifiable_abstract":
                    query_type_guidance = """
QUERY TYPE: QUANTIFIABLE ABSTRACT
This was an abstract question that has been answered using metric-based evidence.
Ensure your report emphasises the quantitative data (numbers, percentages, dollar amounts)
that answer the question. State trends in terms of specific figures, not vague descriptions.
Example: "Board diversity increased from 18% (2/11) in 2017 to 33% (4/12) in 2020" NOT "diversity improved"
"""
                elif self.query_type == "qualitative_abstract":
                    query_type_guidance = """
QUERY TYPE: QUALITATIVE ABSTRACT
This is a qualitative query seeking narrative explanations, rationale, or policy descriptions.
The findings are based on narrative text rather than hard metrics.
Include a note in the report that this answer is based on descriptive content and
some interpretations may be directional rather than precisely quantifiable.
Mark overall confidence as MEDIUM.
"""

                writer_prompt = f"""Original Query: {query}
{query_type_guidance}
Analyst Summary: {analyst_report.summary}

Red Flags Identified: {analyst_report.red_flags}

FINDINGS TO SYNTHESISE:
{findings_text}

Write a professional governance research report. EVERY claim must cite [Chunk ID: xxx]."""

                writer_result = await Runner.run(
                    writer_agent,
                    writer_prompt,
                    max_turns=8
                )
                report = writer_result.final_output_as(ReportData)
                yield "   Done. Report drafted"

            except Exception as e:
                self.errors.append(f"Report writing failed: {str(e)}")
                yield f"   Error in report writing: {str(e)[:100]}"
                report = ReportData(
                    short_summary="Report generation failed due to an error.",
                    markdown_report=f"## Error\n\nCould not generate report: {str(e)[:200]}",
                    claims_made=[],
                    follow_up_questions=["Please try a different query"]
                )

            # Step 4: Verification
            yield "\nStep 4: Verifying citations..."
            try:
                verify_prompt = f"""Verify all claims in this governance research report:

{report.markdown_report}

CLAIMS TO VERIFY:
{json.dumps(report.claims_made, indent=2)}

For each claim:
1. Check if it has a [Chunk ID: xxx] citation
2. Use get_chunk_by_id to retrieve the source
3. Verify the claim matches the source text
4. Mark as VERIFIED, UNSUPPORTED, or HALLUCINATION"""

                verify_result = await Runner.run(
                    verifier_agent,
                    verify_prompt,
                    max_turns=self.max_turns
                )
                verification = verify_result.final_output_as(VerificationResult)

                status = "PASSED" if verification.verified else "ISSUES FOUND"
                yield f"   Done. {status}: {verification.verified_count}/{verification.total_claims} claims verified"

                if verification.hallucinations:
                    yield f"   Warning: {len(verification.hallucinations)} potential hallucinations detected"

            except Exception as e:
                self.errors.append(f"Verification failed: {str(e)}")
                yield f"   Error in verification: {str(e)[:100]}"
                verification = VerificationResult(
                    verified=False,
                    total_claims=len(report.claims_made),
                    verified_count=0,
                    claims=[],
                    hallucinations=["Verification could not be completed"],
                    unsupported=[]
                )

            yield "\nResearch Complete!"

            # Return final output
            yield {
                "query": query,
                "query_type": self.query_type,
                "confidence_level": self.confidence_level,
                "report": report,
                "verification": verification,
                "analyst_report": analyst_report,
                "sources": list(PDF_SOURCES.values()),
                "chunks_used": list(set(self.chunks_retrieved)),
                "trace_id": trace_id,
                "errors": self.errors,
                "sub_queries": clarification.sub_queries if clarification.sub_queries else [],
                "target_metrics": clarification.target_metrics if clarification.target_metrics else [],
            }

async def run_research_async(query: str, progress=gr.Progress()):
    """Execute research pipeline with progress tracking."""
    if not query.strip():
        return "Please enter a research query.", "", "", ""

    if not ALL_CHUNKS:
        return (
            "## Error\n\nNo documents loaded. Please ensure PDF files are in the assets folder.",
            "**Status:** No documents available",
            "{}",
            "Error: No documents loaded"
        )

    manager = GovernanceResearchManager()
    status_updates = []
    output = None

    progress(0, desc="Initialising...")

    try:
        async for update in manager.run(query):
            if isinstance(update, str):
                status_updates.append(update)
                if "Step 1" in update:
                    progress(0.15, desc="Clarifying query...")
                elif "Step 2" in update:
                    progress(0.35, desc="Analysing documents...")
                elif "Step 3" in update:
                    progress(0.60, desc="Writing report...")
                elif "Step 4" in update:
                    progress(0.80, desc="Verifying citations...")
                elif "Complete" in update:
                    progress(0.95, desc="Finalising...")
            else:
                output = update
    except Exception as e:
        progress(1.0, desc="Error")
        error_msg = f"Research pipeline error: {str(e)}"
        return (
            f"## Error\n\n{error_msg}",
            "**Status:** Failed",
            "{}",
            "\n".join(status_updates) + f"\n\nERROR: {error_msg}"
        )

    progress(1.0, desc="Done!")

    if not output:
        return (
            "## Error\n\nResearch failed to produce results.",
            "**Status:** No output",
            "{}",
            "\n".join(status_updates)
        )

    # Format the report
    report_md = output["report"].markdown_report

    # Format verification status
    v = output["verification"]
    if v.verified:
        status_emoji = "✓"
        status_color = "green"
    elif v.verified_count > v.total_claims * 0.5:
        status_emoji = "⚠"
        status_color = "orange"
    else:
        status_emoji = "✗"
        status_color = "red"

    # Query type display
    query_type = output.get("query_type", "concrete")
    confidence = output.get("confidence_level", "high")

    query_type_display = {
        "concrete": "📊 Concrete (fact-based)",
        "quantifiable_abstract": "📈 Abstract → Metrics (decomposed)",
        "qualitative_abstract": "📝 Qualitative (narrative-based)"
    }.get(query_type, query_type)

    confidence_display = {
        "high": "🟢 High",
        "medium": "🟡 Medium",
        "low": "🔴 Low"
    }.get(confidence, confidence)

    status_text = f"""## Research Complete {status_emoji}

**Query Type:** {query_type_display}

**Confidence Level:** {confidence_display}

**Verification Status:** {v.verified_count}/{v.total_claims} claims verified

**Chunks Analysed:** {len(output['chunks_used'])}

**Trace ID:** `{output['trace_id']}`
"""

    # Show sub-queries if used
    if output.get("sub_queries"):
        status_text += f"\n**Decomposed into {len(output['sub_queries'])} metric-seeking sub-queries**"

    if v.hallucinations:
        status_text += f"\n\n**⚠ Potential Issues:** {len(v.hallucinations)} unverified claims"

    if output.get("errors"):
        status_text += f"\n\n**Pipeline Warnings:** {len(output['errors'])}"

    # Add confidence warning for qualitative queries
    if query_type == "qualitative_abstract":
        status_text += "\n\n*Note: This was a qualitative query. Findings are based on narrative descriptions rather than hard metrics. Some interpretations may be directional.*"

    # Format provenance data
    provenance_data = {
        "query": output["query"],
        "query_classification": {
            "type": output.get("query_type", "concrete"),
            "confidence_level": output.get("confidence_level", "high"),
            "sub_queries": output.get("sub_queries", []),
            "target_metrics": output.get("target_metrics", []),
        },
        "trace_id": output["trace_id"],
        "sources": [
            {
                "file": s.filename,
                "company": s.company,
                "year": s.year,
                "sha256": s.sha256_hash[:40] + "...",
                "total_pages": s.total_pages
            }
            for s in output["sources"]
        ],
        "chunks_used": output["chunks_used"],
        "verification": {
            "verified": v.verified,
            "verified_count": v.verified_count,
            "total_claims": v.total_claims,
            "hallucinations": v.hallucinations,
            "unsupported": v.unsupported
        },
        "errors": output.get("errors", [])
    }

    provenance_json = json.dumps(provenance_data, indent=2)

    return report_md, status_text, provenance_json, "\n".join(status_updates)

def run_research(query, progress=gr.Progress()):
    return asyncio.run(run_research_async(query, progress))

def verify_chunk(chunk_id):
    if not chunk_id.strip():
        return "Enter a chunk ID"
    return _get_chunk_by_id(chunk_id.strip())

def get_pdf_path(filename, page):
    path = ASSETS_DIR / filename
    if path.exists():
        abs_path = str(path.resolve())
        return f'''
        <div style="padding:24px; background:linear-gradient(135deg, #1e3a5f 0%, #0d1b2a 100%); border-radius:12px; border:1px solid #3d5a80; font-family:system-ui;">
            <h3 style="color:#e0e1dd; margin:0 0 16px 0; font-size:18px;">📄 {filename}</h3>
            <div style="background:#0d1b2a; padding:12px 16px; border-radius:8px; margin-bottom:16px;">
                <code style="color:#98c1d9; font-size:13px; word-break:break-all;">{abs_path}</code>
            </div>
            <div style="display:flex; align-items:center; gap:12px;">
                <span style="background:#ee6c4d; color:white; padding:8px 16px; border-radius:6px; font-weight:600;">Page {int(page) if page is not None else 'unknown'}</span>
                <span style="color:#98c1d9; font-size:14px;">Open in your PDF reader to verify</span>
            </div>
        </div>
        '''
    return f"PDF not found: {path}"


def create_app():
    with gr.Blocks(title="Governance Research Agent", theme=gr.themes.Soft(primary_hue="orange", neutral_hue="slate")) as app:
        gr.Markdown("# Governance Research Agent\n**Analyse BHP Annual Reports (2016-2020) with forensic-grade citations**")
        with gr.Row():
            with gr.Column(scale=1):
                query_input = gr.Textbox(label="Research Query", placeholder="e.g., Analyse BHP CEO remuneration trends from 2018 to 2020", lines=2)
                run_btn = gr.Button("Run Research", variant="primary")
                with gr.Accordion("Status Log", open=False):
                    status_log = gr.Textbox(label="Log", lines=6, interactive=False)
                status_summary = gr.Markdown()
                gr.Markdown("### Report")
                report_output = gr.Markdown()
            with gr.Column(scale=1):
                gr.Markdown("### Verify Citation")
                with gr.Row():
                    chunk_input = gr.Textbox(label="Chunk ID", placeholder="bhp_2019_p152_c1033", scale=3)
                    verify_btn = gr.Button("Verify", scale=1)
                chunk_content = gr.Markdown()
                gr.Markdown("### PDF Viewer")
                with gr.Row():
                    pdf_select = gr.Dropdown(choices=[p["filename"] for p in PDF_FILES], label="PDF", value="BHP_19AR.pdf")
                    page_num = gr.Number(label="Page", value=1, minimum=1)
                    go_btn = gr.Button("Go")
                pdf_viewer = gr.HTML()
        with gr.Accordion("Provenance", open=False):
            provenance_json = gr.Code(language="json")
        gr.Examples([["Analyse BHP CEO remuneration trends from 2018 to 2020"], ["What was Andrew Mackenzie's total pay in FY2019?"], ["Compare executive compensation between 2016 and 2020"]], inputs=query_input)
        run_btn.click(run_research, [query_input], [report_output, status_summary, provenance_json, status_log])
        verify_btn.click(verify_chunk, [chunk_input], [chunk_content])
        go_btn.click(get_pdf_path, [pdf_select, page_num], [pdf_viewer])
    return app

if __name__ == "__main__":
    print("Governance Research Agent")
    print("=" * 50)
    print("Loading PDFs...")
    extract_all_pdfs()
    print(f"Loaded {len(ALL_CHUNKS):,} chunks from {len(PDF_SOURCES)} PDFs")
    app = create_app()
    app.launch(share=True, allowed_paths=[str(ASSETS_DIR)])
