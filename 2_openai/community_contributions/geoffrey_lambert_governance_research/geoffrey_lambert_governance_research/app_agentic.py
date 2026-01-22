"""
Governance Research Agent - AGENTIC ORCHESTRATION VERSION

This version demonstrates Ed Donner's Week 2 pattern:
- Agents as tools (.as_tool())
- Manager agent with tools and handoffs
- LLM-driven orchestration (agent decides flow)

Compare with app.py which uses workflow orchestration (Python controls flow).

Key difference: Here, the ResearchManager is an LLM Agent that autonomously
decides which tools to call and when to hand off. In app.py, a Python class
explicitly controls the pipeline sequence.
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

# =============================================================================
# CONFIGURATION - Same as app.py
# =============================================================================

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
    "max_turns": 30,  # Higher for agentic - manager needs more turns
    "min_chunk_length": 100,
    "bm25_k1": 1.5,
    "bm25_b": 0.75,
}

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

# =============================================================================
# PYDANTIC MODELS - Same as app.py
# =============================================================================

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
    """Output from the Clarifier Agent"""
    questions: list[str] = Field(description="2-3 clarifying questions to refine the research")
    refined_query: str = Field(description="A clear, keyword-rich version of the query")
    identified_years: list[int] = Field(description="Years to focus on (e.g., [2019, 2020])")
    focus_areas: list[str] = Field(description="Relevant sections to searcdemoh")
    query_type: Literal["concrete", "quantifiable_abstract", "qualitative_abstract"] = "concrete"
    sub_queries: list[str] = Field(default=[], description="Metric-seeking sub-queries for abstract questions")
    target_metrics: list[str] = Field(default=[], description="Expected metrics to find")

class AnalystFinding(BaseModel):
    finding: str
    evidence: str
    chunk_id: str
    page: int
    confidence: str = "high"
    category: str

class AnalystReport(BaseModel):
    """Output from the Analyst Agent"""
    analyst_name: str
    findings: list[AnalystFinding]
    summary: str
    red_flags: list[str] = []

class ReportData(BaseModel):
    """Output from the Writer Agent"""
    short_summary: str = Field(description="A short 2-3 sentence summary")
    markdown_report: str = Field(description="The full report in markdown")
    claims_made: list[str] = Field(description="List of factual claims in the report")
    follow_up_questions: list[str] = Field(description="Suggested follow-up research")

class ClaimVerification(BaseModel):
    claim: str
    status: str
    source_chunk_id: Optional[str] = None
    source_text: Optional[str] = None

class VerificationResult(BaseModel):
    """Output from the Verifier Agent"""
    verified: bool
    total_claims: int
    verified_count: int
    claims: list[ClaimVerification]
    hallucinations: list[str] = []
    unsupported: list[str] = []
    original_report: str = Field(default="", description="The original report that was verified")

# =============================================================================
# INFRASTRUCTURE - Same as app.py (PDF loading, chunking, search)
# =============================================================================

PDF_SOURCES = {}
ALL_CHUNKS = {}
IDF_SCORES = {}

def compute_sha256(file_path):
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            sha256_hash.update(chunk)
    return sha256_hash.hexdigest()

def detect_section(text: str) -> str:
    text_lower = text.lower()
    section_patterns = {
        "Remuneration Report": ["remuneration", "compensation", "kmp", "executive pay", "salary", "bonus", "incentive"],
        "Directors Report": ["board of directors", "director's report", "non-executive director", "chairman"],
        "Corporate Governance": ["corporate governance", "governance framework", "asx corporate governance"],
        "Financial Statements": ["consolidated statement", "balance sheet", "income statement", "cash flow"],
        "Risk Management": ["risk management", "risk factor", "principal risk", "operational risk"],
        "Sustainability": ["sustainability", "environmental", "climate change", "emissions", "safety performance"],
        "Operations Review": ["operations review", "production", "petroleum", "minerals", "copper", "iron ore"],
    }
    scores = {}
    for section, keywords in section_patterns.items():
        score = sum(1 for kw in keywords if kw in text_lower)
        if score > 0:
            scores[section] = score
    return max(scores, key=scores.get) if scores else "General"

def tokenize(text: str) -> List[str]:
    tokens = re.findall(r'\b[a-z0-9]+\b', text.lower())
    return [t for t in tokens if t not in STOPWORDS and len(t) > 2]

def compute_idf(corpus_chunks: Dict[str, DocumentChunk]) -> Dict[str, float]:
    doc_count = len(corpus_chunks)
    if doc_count == 0:
        return {}
    doc_freq = Counter()
    for chunk in corpus_chunks.values():
        unique_terms = set(tokenize(chunk.content))
        doc_freq.update(unique_terms)
    idf = {}
    for term, freq in doc_freq.items():
        idf[term] = math.log((doc_count - freq + 0.5) / (freq + 0.5) + 1)
    return idf

def clean_text(text: str) -> str:
    text = re.sub(r'[ \t]+', ' ', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = re.sub(r'^\d+\s*$', '', text, flags=re.MULTILINE)
    return text.strip()

def find_sentence_boundary(text: str, position: int, direction: str = "backward") -> int:
    sentence_endings = re.compile(r'[.!?][\s\n]')
    if direction == "backward":
        search_text = text[:position]
        matches = list(sentence_endings.finditer(search_text))
        if matches:
            return matches[-1].end()
        return 0
    else:
        search_text = text[position:]
        match = sentence_endings.search(search_text)
        if match:
            return position + match.end()
        return len(text)

def extract_pdf_chunks(pdf_path: Path, company: str, year: int) -> Tuple[PDFSource, List[DocumentChunk]]:
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
        except:
            continue
        text = clean_text(text)
        if not text or len(text) < min_length:
            continue

        start = 0
        while start < len(text):
            tentative_end = start + chunk_size
            if tentative_end >= len(text):
                chunk_text = text[start:].strip()
            else:
                boundary = find_sentence_boundary(text[:tentative_end], tentative_end, "backward")
                search_start = start + int(chunk_size * 0.7)
                if boundary > search_start:
                    chunk_text = text[start:boundary].strip()
                    tentative_end = boundary
                else:
                    chunk_text = text[start:tentative_end].strip()

            if chunk_text and len(chunk_text) >= min_length:
                chunk_id = f"{company.lower()}_{year}_p{page_num + 1:03d}_c{chunk_counter:03d}"
                chunks.append(DocumentChunk(
                    chunk_id=chunk_id, content=chunk_text, company=company,
                    year=year, page=page_num + 1, section=detect_section(chunk_text),
                    source_file=str(pdf_path)
                ))
                chunk_counter += 1

            new_start = tentative_end - chunk_overlap
            if new_start <= start:
                new_start = start + min_length
            start = new_start

    doc.close()
    return source, chunks

def extract_all_pdfs():
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

    print("   Computing IDF scores...", end=" ", flush=True)
    IDF_SCORES = compute_idf(ALL_CHUNKS)
    print(f"{len(IDF_SCORES)} terms indexed")

# =============================================================================
# FUNCTION TOOLS - Search capabilities for the Analyst
# =============================================================================

@function_tool
def search_annual_reports(
    keywords: str,
    company: str = "BHP",
    years: Optional[List[int]] = None,
    sections: Optional[List[str]] = None,
    max_results: int = 10
) -> str:
    """
    Search BHP annual reports for specific keywords.
    Returns matching chunks with their IDs for citation.
    """
    if not ALL_CHUNKS:
        return "ERROR: No documents loaded."

    query_tokens = tokenize(keywords)
    if not query_tokens:
        return "ERROR: No valid search terms."

    all_lengths = [len(tokenize(c.content)) for c in ALL_CHUNKS.values()]
    avg_doc_len = sum(all_lengths) / len(all_lengths) if all_lengths else 100

    results = []
    k1, b = CONFIG["bm25_k1"], CONFIG["bm25_b"]

    for chunk_id, chunk in ALL_CHUNKS.items():
        if chunk.company.upper() != company.upper():
            continue
        if years and chunk.year not in years:
            continue
        if sections and not any(s.lower() in chunk.section.lower() for s in sections):
            continue

        doc_tokens = tokenize(chunk.content)
        doc_len = len(doc_tokens)
        term_freq = Counter(doc_tokens)

        score = 0.0
        for term in query_tokens:
            if term in term_freq:
                tf = term_freq[term]
                idf = IDF_SCORES.get(term, 1.0)
                tf_component = (tf * (k1 + 1)) / (tf + k1 * (1 - b + b * (doc_len / avg_doc_len)))
                score += idf * tf_component

        if score > 0:
            results.append((chunk, score))

    results.sort(key=lambda x: x[1], reverse=True)
    top_results = results[:max_results]

    if not top_results:
        return f"No results found for '{keywords}'"

    output = [f"## Search Results for '{keywords}'\n"]
    for chunk, score in top_results:
        output.append(f"**[Chunk ID: {chunk.chunk_id}]** (Page {chunk.page}, {chunk.section})")
        output.append(f"Score: {score:.2f}")
        content_preview = chunk.content[:500] + "..." if len(chunk.content) > 500 else chunk.content
        output.append(f"Content: {content_preview}\n")

    return "\n".join(output)

@function_tool
def get_chunk_by_id(chunk_id: str) -> str:
    """Retrieve full content of a specific chunk by its ID."""
    if chunk_id not in ALL_CHUNKS:
        return f"ERROR: Chunk ID '{chunk_id}' not found."
    c = ALL_CHUNKS[chunk_id]
    return f"**Chunk ID:** {c.chunk_id}\n**Source:** {c.company} {c.year} AR, Page {c.page}\n**Section:** {c.section}\n\n**Content:**\n{c.content}"

@function_tool
def list_available_years(company: str = "BHP") -> str:
    """List available years of annual reports."""
    years = set(c.year for c in ALL_CHUNKS.values() if c.company.upper() == company.upper())
    return f"Available years for {company}: {sorted(years)}" if years else f"No data for {company}"

# =============================================================================
# SPECIALIST AGENTS - Same logic as app.py but will be converted to tools
# =============================================================================

CLARIFIER_INSTRUCTIONS = """You are a governance research query clarification specialist.

Your task is to analyse user queries and prepare them for high-accuracy document retrieval.

Given a query about BHP annual reports (2016-2020), you must:

1. Generate 2-3 CLARIFYING QUESTIONS that could refine the research
2. Create a REFINED QUERY with specific keywords for searching
3. Identify which YEARS to focus on (default: [2019, 2020])
4. Identify FOCUS AREAS (sections like "Remuneration Report", "Corporate Governance", etc.)
5. Classify QUERY TYPE:
   - "concrete": Specific facts (e.g., "What was CEO pay in 2019?")
   - "quantifiable_abstract": Trends that need metrics (e.g., "How did pay change over time?")
   - "qualitative_abstract": Narrative/policy questions (e.g., "What was the pay philosophy?")
6. For quantifiable_abstract queries, generate 3-5 SUB-QUERIES to find specific metrics

Return all fields in the ClarifyingQuestions schema.
"""

clarifier_agent = Agent(
    name="ClarifierAgent",
    instructions=CLARIFIER_INSTRUCTIONS,
    model=CONFIG["default_model"],
    output_type=ClarifyingQuestions,
)

ANALYST_INSTRUCTIONS = """You are a governance analyst for BHP annual reports.

You have access to search tools. Your job is to:
1. Search for relevant information using the refined query and years provided
2. Extract 3-5 key findings with specific evidence
3. Every finding MUST include a Chunk ID for citation
4. Note any red flags or unusual patterns

Use search_annual_reports to find relevant chunks, then compile findings.
Include exact figures (dollar amounts, percentages) where available.
"""

analyst_agent = Agent(
    name="AnalystAgent",
    instructions=ANALYST_INSTRUCTIONS,
    tools=[search_annual_reports, get_chunk_by_id, list_available_years],
    model=CONFIG["default_model"],
    output_type=AnalystReport,
)

WRITER_INSTRUCTIONS = """You are a professional governance report writer.

You receive analyst findings and must synthesise them into a clear report.

RULES:
1. Use ONLY the findings provided - no external knowledge
2. EVERY factual claim MUST include a citation [Chunk ID: xxx]
3. Structure: Executive Summary, Key Findings, Detailed Analysis, Red Flags, Recommendations
4. Be precise with numbers and dates

SENSITIVE CLAIM MODE:
For claims about fatalities, safety incidents, or legal matters:
- Use EXACT language from source
- Do NOT paraphrase cause, preventability, or fault
- When uncertain, quote directly: 'The report states "..."'
"""

writer_agent = Agent(
    name="WriterAgent",
    instructions=WRITER_INSTRUCTIONS,
    model=CONFIG["default_model"],
    output_type=ReportData,
)

VERIFIER_INSTRUCTIONS = """You are a forensic verification specialist.

You receive a report and the source chunks used. Your job is to:
1. Extract each factual claim from the report
2. Check if the claim is supported by the cited chunk
3. Flag any hallucinations (claims not supported by evidence)
4. Flag any unsupported claims (claims without citations)
5. IMPORTANT: Include the original report in your output (original_report field)

Be strict - if a claim cannot be verified from the chunks, mark it as unverified.
Always preserve and return the original report text in the original_report field.
"""

verifier_agent = Agent(
    name="VerifierAgent",
    instructions=VERIFIER_INSTRUCTIONS,
    model=CONFIG["default_model"],
    output_type=VerificationResult,
    handoff_description="Verify report claims against source documents and return final verification",
)

# =============================================================================
# AGENTIC ORCHESTRATION - The key difference from app.py
# =============================================================================

# Convert specialist agents to TOOLS (Ed's Week 2 pattern)
clarifier_tool = clarifier_agent.as_tool(
    tool_name="clarify_query",
    tool_description="Analyse the user query, generate clarifying questions, identify years and focus areas, and create a refined search query. Call this FIRST."
)

analyst_tool = analyst_agent.as_tool(
    tool_name="analyse_documents",
    tool_description="Search BHP annual reports and extract findings based on the clarified query. Requires clarification output. Returns findings with citations."
)

writer_tool = writer_agent.as_tool(
    tool_name="write_report",
    tool_description="Synthesise analyst findings into a formatted governance report with citations. Requires analyst findings."
)

# The Manager Agent - orchestrates the pipeline using tools and handoffs
MANAGER_INSTRUCTIONS = """You are the Research Manager for governance analysis of BHP annual reports.

You orchestrate a research pipeline by using your tools and then handing off for verification.

WORKFLOW - Follow these steps in order:

1. CLARIFY: First, use the clarify_query tool to analyse the user's query.
   Pass the user's exact query. Get back clarifying questions, refined query, years, and focus areas.

2. ANALYSE: Use the analyse_documents tool with the clarification output.
   Tell it the refined query, years to search, and focus areas.
   Get back findings with chunk IDs.

3. WRITE: Use the write_report tool with the analyst findings.
   Pass all the findings so they can be synthesised into a report.
   Get back a formatted report with citations.

4. HANDOFF: Once you have the report, hand off to the VerifierAgent.
   The verifier will check all claims against sources and return the final result.

IMPORTANT:
- Call tools in order: clarify -> analyse -> write -> handoff to verifier
- Pass relevant context between steps
- The verifier handoff is the FINAL step - after that, the pipeline is complete
"""

research_manager = Agent(
    name="ResearchManager",
    instructions=MANAGER_INSTRUCTIONS,
    tools=[clarifier_tool, analyst_tool, writer_tool],  # Agents as tools
    handoffs=[verifier_agent],                           # Handoff for final verification
    model=CONFIG["strong_model"],  # Use stronger model for orchestration
)

# =============================================================================
# RUN FUNCTION - Much simpler than app.py's workflow
# =============================================================================

async def run_agentic_research(query: str):
    """
    Execute research using agentic orchestration.

    The manager agent autonomously decides:
    - Which tools to call
    - What to pass between tools
    - When to hand off to verifier
    """
    if not query.strip():
        return "Please enter a research query.", "", "{}"

    # Ensure PDFs are loaded (handles dev mode / reload scenarios)
    if not ALL_CHUNKS:
        print("Documents not loaded - loading now...")
        extract_all_pdfs()

    if not ALL_CHUNKS:
        return "No documents loaded. Please ensure PDFs are in assets folder.", "", "{}"

    trace_id = gen_trace_id()

    with trace("Agentic Governance Research", trace_id=trace_id):
        try:
            # Single call - manager orchestrates everything
            result = await Runner.run(
                research_manager,
                query,
                max_turns=CONFIG["max_turns"]
            )

            # The result comes from the verifier (via handoff)
            final_output = result.final_output

            # Try to extract structured output
            if hasattr(final_output, 'verified'):
                # Verifier output (from handoff)
                verification_status = f"{final_output.verified_count}/{final_output.total_claims} claims verified"

                # Get the original report if available
                if hasattr(final_output, 'original_report') and final_output.original_report:
                    report = final_output.original_report
                    report += f"\n\n---\n\n## Verification Summary\n\n"
                    report += f"**Verified:** {final_output.verified_count}/{final_output.total_claims} claims\n\n"
                else:
                    report = f"## Verification Complete\n\n"
                    report += f"**Verified:** {final_output.verified_count}/{final_output.total_claims} claims\n\n"

                if final_output.hallucinations:
                    report += f"**Hallucinations detected:** {final_output.hallucinations}\n\n"
                if final_output.unsupported:
                    report += f"**Unsupported claims:** {final_output.unsupported}\n\n"

            elif hasattr(final_output, 'markdown_report'):
                report = final_output.markdown_report
                verification_status = "Report generated (not verified)"
            else:
                report = str(final_output)
                verification_status = "Complete"

            status = f"""## Agentic Research Complete

**Orchestration:** Manager Agent with Tools + Handoff

**Trace:** [{trace_id}](https://platform.openai.com/traces/{trace_id})

**Status:** {verification_status}

*This used agentic orchestration - the manager LLM decided the flow.*
"""

            provenance = {
                "trace_id": trace_id,
                "orchestration": "agentic",
                "manager": "ResearchManager",
                "tools_available": ["clarify_query", "analyse_documents", "write_report"],
                "handoff_to": "VerifierAgent",
            }

            return report, status, json.dumps(provenance, indent=2)

        except Exception as e:
            error_msg = f"## Error\n\nAgentic pipeline failed: {str(e)}"
            return error_msg, f"**Error:** {str(e)[:100]}", "{}"

def run_research_sync(query):
    """Synchronous wrapper for Gradio."""
    return asyncio.run(run_agentic_research(query))

# =============================================================================
# GRADIO UI - Same layout as app.py but on different port
# =============================================================================

def create_app():
    with gr.Blocks(
        title="Governance Research Agent (AGENTIC)",
        theme=gr.themes.Soft(primary_hue="blue", neutral_hue="slate")
    ) as app:
        gr.Markdown("""# Governance Research Agent - AGENTIC VERSION

**This version uses Ed Donner's Week 2 pattern: Agents as Tools + Handoffs**

Compare with `app.py` (workflow orchestration) to see the difference.
- Here: Manager Agent decides the flow autonomously
- app.py: Python code controls the pipeline explicitly
""")

        with gr.Row():
            with gr.Column(scale=1):
                query_input = gr.Textbox(
                    label="Research Query",
                    placeholder="e.g., How did board diversity change between 2016 and 2020?",
                    lines=2
                )
                run_btn = gr.Button("Run Agentic Research", variant="primary")
                status_output = gr.Markdown(label="Status")

            with gr.Column(scale=1):
                gr.Markdown("### Report")
                report_output = gr.Markdown()

        with gr.Accordion("Provenance (Agentic)", open=False):
            provenance_output = gr.Code(language="json")

        gr.Examples(
            examples=[
                ["How did board gender diversity change between 2016 and 2020?"],
                ["What was Andrew Mackenzie's total remuneration in FY2019?"],
                ["What were the TRIFR safety metrics and fatalities from 2017 to 2020?"],
            ],
            inputs=query_input
        )

        run_btn.click(
            run_research_sync,
            inputs=[query_input],
            outputs=[report_output, status_output, provenance_output]
        )

    return app

# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("AGENTIC ORCHESTRATION VERSION")
    print("This demonstrates Ed's Week 2 pattern: Agents as Tools + Handoffs")
    print("=" * 60)
    print("\nLoading PDFs...")
    extract_all_pdfs()
    print(f"Loaded {len(ALL_CHUNKS):,} chunks from {len(PDF_SOURCES)} PDFs")
    print("\nStarting Gradio app on port 7861...")
    print("(app.py runs on 7860, so you can run both simultaneously)")
    app = create_app()
    app.launch(server_port=7861, share=True)
