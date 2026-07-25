# Homepage Builder

Automated AI-driven pipeline to research local businesses and generate high-quality, W3C-compliant homepages.

## GOAL
The mission of **Homepage Builder** is to provide local Small and Medium-sized Businesses (SMBs) with a professional online presence. The project automates the entire lifecycle:
1.  **Discover**: Find active local businesses in a specific area using Google Search.
2.  **Analyze**: Scrape their existing websites to understand their services and sector.
3.  **Design & Build**: Use specialized agents to draft a modern design and code it into a single-file Tailwind CSS homepage.
4.  **Audit & Amend**: Perform automated technical and accessibility (WCAG) reviews, then loop back to fix any issues, ensuring a premium, compliant final product.

## TECH STACK
- **Framework**: [CrewAI](https://crewai.com) for multi-agent orchestration.
- **LLMs**: Google Gemini (via `google-genai`) for reasoning, design guidance, and coding.
- **Search**: [Serper](https://serper.dev) for business discovery.
- **Scraping**: [Firecrawl](https://firecrawl.dev) for deep website content extraction.
- **Styling**: Tailwind CSS (CDN-based) for responsive, professional UI.
- **Runtime**: Python 3.10+ with [UV](https://github.com/astral-sh/uv) for high-performance dependency management.

## TECH HIGHLIGHTS
- **Multi-Crew Orchestration**: Split into `ResearcherCrew`, `ScraperCrew`, and `BuildAndReviewCrew` for maximum reliability and scalability.
- **Hierarchical Review Loop**: A dedicated manager agent coordinates `Technical Review` and `Accessibility Review` agents to audit the initial draft.
- **Agent Memory**: Persistent memory allows the `Web Designer` and `Frontend Developer` to learn from review feedback and amend the code in a single execution flow.
- **Batch Processing**: Natively handles multiple businesses in a single execution via `kickoff_for_each`.
- **W3C Accessibility First**: Built-in enforcement of semantic HTML, ARIA landmarks, and WCAG-compliant color contrast.

## USAGE

### 1. Prerequisite Setup
Configure your `.env` file with the following keys:
```env
GOOGLE_API_KEY=...
SERPER_API_KEY=...
FIRECRAWL_API_KEY=...
```

### 2. Configuration
In `src/homepage_builder/main.py`, define your search criteria:
```python
inputs = {
    'number_of_businesses': 3,
    'geographical_area': 'San Francisco, CA'
}
```

### 3. Execution
Run the full pipeline:
```bash
uv run crewai run
```

### 4. Output
Generated files will be saved in the `output/` directory:
- `{company_name}.html`: Initial generation.
- `{company_name}_tech_review.md`: Automated technical audit.
- `{company_name}_accessibility_review.md`: W3C/WCAG compliance report.
- `{company_name}_amended.html`: Final corrected version incorporating all review feedback.
