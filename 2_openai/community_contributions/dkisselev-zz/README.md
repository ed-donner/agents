# 🧬 Pharmacogenomic Clinical Report Generator

An AI-powered multi-agent system for generating pharmacogenomic clinical reports in oncology and precision medicine.

## Overview

This system integrates multiple specialized AI agents to search biomedical databases, synthesize findings, and generate professional reports focused on cancer pharmacogenomics and personalized medicine.

### Key Features

- **Multi-Database Search**: Parallel searches across PubMed, ClinicalTrials.gov, and PharmGKB
- **Query Parsing**: Automatically extracts disease, genes, mutations, and clinical context
- **Reports**: Structured reports with evidence-based recommendations
- **HTML Output**: HTML reports with custom styling
- **Email Integration**: Automated email delivery via Mailgun API

## Architecture

### Agent System

The system uses a coordinated multi-agent architecture:

1. **QueryParserAgent**: Extracts structured clinical information (disease, genes, mutations)
2. **MedicalPlannerAgent**: Plans searches across three specialized databases
3. **PubMedAgent**: Searches biomedical literature using NCBI E-utilities
4. **ClinicalTrialsAgent**: Queries ClinicalTrials.gov for ongoing/completed trials
5. **PharmGKBAgent**: Searches pharmacogenomic drug-gene interactions
6. **ClinicalWriterAgent**: Synthesizes findings into a comprehensive report
7. **EmailAgent**: Delivers reports via Mailgun

### Data Flow

```
User Query
    ↓
QueryParserAgent (extracts: disease, genes, mutations)
    ↓
MedicalPlannerAgent (plans 6 searches: 2 PubMed, 2 ClinicalTrials, 2 PharmGKB)
    ↓
Parallel Search Execution (3 specialized agents)
    ↓
ClinicalWriterAgent (synthesizes comprehensive report)
    ↓
HTML Report Generator + Email Delivery
```

## Installation

### Prerequisites

- Python 3.11 or higher
- `uv` package manager
- OpenAI API key
- Mailgun API key (for email functionality)

### Setup

1. Install dependencies with `uv`:

```bash
uv sync
```

2. Add API kleys to `.env`:

```env
# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key_here

# Mailgun Configuration
MAILGUN_API_KEY=your_mailgun_api_key_here
MAILGUN_DOMAIN=your-domain.mailgun.org
MAILGUN_FROM_EMAIL=Clinical Reports <noreply@your-domain.mailgun.org>
EMAIL_ADDRESS=your-email@example.com
```

## Usage

### Running the Application

Start the Gradio web interface:

```bash
uv run python deep_research.py
```

### Example Queries

**NSCLC with EGFR T790M**:
```
Patient has non-small cell lung cancer (NSCLC) with an EGFR T790M mutation. 
What are the indicated therapies and resistance mechanisms?
```

**Melanoma with BRAF V600E**:
```
What are the treatment options for metastatic melanoma with BRAF V600E mutation?
```

**Breast Cancer with HER2**:
```
Breast cancer patient with HER2 amplification - what targeted therapies are 
available and what are the latest clinical trials?
```

**CML with BCR-ABL T315I**:
```
Patient with chronic myeloid leukemia (CML) has developed BCR-ABL T315I mutation. 
What are the resistance mechanisms and treatment alternatives?
```

**Colorectal Cancer**:
```
Colorectal cancer with KRAS G12C mutation - what are the emerging treatment options?
```

## Report Structure

Generated reports include the following sections:

1. **Executive Summary**: Key findings and actionable information
2. **Disease and Mutation Overview**: Clinical context and molecular mechanisms
3. **FDA-Approved Therapies**: Current standard-of-care treatments with evidence
4. **Resistance Mechanisms**: Known resistance pathways and secondary mutations
5. **Emerging Research & Clinical Trials**: Novel approaches and active trials
6. **Pharmacogenomic Considerations**: Drug-gene interactions and biomarkers
7. **References**: Citations (PMIDs, NCT IDs, PharmGKB links)

## Output Files

- **HTML Reports**: Saved to `reports/clinical_report_YYYYMMDD_HHMMSS.html`
- **Email**: Automatically sent via Mailgun to configured recipient

## API Integrations

### PubMed (NCBI E-utilities)
- **Endpoint**: https://eutils.ncbi.nlm.nih.gov/entrez/eutils/
- **Authentication**: None required (rate limited to 3 requests/second)
- **Usage**: Biomedical literature search and article summaries

### ClinicalTrials.gov API v2
- **Endpoint**: https://clinicaltrials.gov/api/v2/studies
- **Authentication**: None required
- **Usage**: Clinical trial search with filtering by phase, status, and intervention

### PharmGKB
- **Method**: PubMed search for PharmGKB-annotated literature
- **Note**: Direct PharmGKB API requires authentication, so we use curated PubMed searches
- **Usage**: Pharmacogenomic drug-gene interaction information

### Mailgun Email API
- **Endpoint**: https://api.mailgun.net/v3
- **Authentication**: API key required
- **Usage**: HTML email delivery

## Project Structure

```
dkisselev-zz/
├── deep_research.py              # Main Gradio UI application
├── research_manager.py           # Orchestrates the research workflow
├── query_parser_agent.py         # Parses clinical queries
├── planner_agent.py              # Plans database searches
├── pubmed_agent.py               # PubMed search agent
├── clinical_trials_agent.py      # ClinicalTrials.gov search agent
├── pharmgkb_agent.py             # PharmGKB search agent
├── clinical_writer_agent.py      # Report synthesis agent
├── email_agent.py                # Mailgun email delivery
├── html_report_generator.py      # HTML report formatting
├── requirements.txt              # Python dependencies
├── README.md                     # This file
├── .env                          # Environment variables
└── reports/                      # Generated HTML reports directory
```
