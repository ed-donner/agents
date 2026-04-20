"""
Configuration for Governance Research Agent
"""
import os
from pathlib import Path

# Paths
PROJECT_ROOT = Path(__file__).parent
ASSETS_DIR = PROJECT_ROOT / "assets"
EXTRACTED_DIR = PROJECT_ROOT / "extracted"

# Model settings
CONFIG = {
    # Models
    "default_model": "gpt-4o-mini",
    "strong_model": "gpt-4o",  # For verification tasks
    
    # Retrieval settings
    "retrieval_top_k": 30,      # Candidates before reranking
    "rerank_top_k": 5,          # Final results after reranking
    
    # Agent loop settings
    "max_iterations": 3,        # Max refinement loops
    "max_searches_per_plan": 5, # Max parallel searches
    
    # Paths
    "pdf_directory": str(ASSETS_DIR),
    "extracted_directory": str(EXTRACTED_DIR),
    
    # Email (optional)
    "email_from": os.environ.get("EMAIL_FROM", "research@example.com"),
    "email_to": os.environ.get("EMAIL_TO", "user@example.com"),
}

# Whitelist of trusted regulatory sources for supplementary web search
REGULATORY_SOURCES = {
    "asic": {
        "name": "ASIC",
        "icon": "🏛️",
        "domains": ["asic.gov.au"],
        "search_prefix": "site:asic.gov.au",
        "description": "Australian Securities & Investments Commission"
    },
    "asx": {
        "name": "ASX Announcements",
        "icon": "📈",
        "domains": ["asx.com.au"],
        "search_prefix": "site:asx.com.au",
        "description": "ASX company announcements and filings"
    },
    "federal_court": {
        "name": "Federal Court",
        "icon": "⚖️",
        "domains": ["judgments.fedcourt.gov.au", "fedcourt.gov.au"],
        "search_prefix": "site:fedcourt.gov.au",
        "description": "Federal Court of Australia judgments"
    },
    "takeovers_panel": {
        "name": "Takeovers Panel",
        "icon": "🔄",
        "domains": ["takeovers.gov.au"],
        "search_prefix": "site:takeovers.gov.au",
        "description": "Takeovers Panel decisions and guidance"
    },
    "apra": {
        "name": "APRA",
        "icon": "🏦",
        "domains": ["apra.gov.au"],
        "search_prefix": "site:apra.gov.au",
        "description": "Australian Prudential Regulation Authority"
    },
    "accc": {
        "name": "ACCC",
        "icon": "⚡",
        "domains": ["accc.gov.au"],
        "search_prefix": "site:accc.gov.au",
        "description": "Competition & consumer matters"
    },
    "austlii": {
        "name": "AustLII",
        "icon": "📚",
        "domains": ["austlii.edu.au"],
        "search_prefix": "site:austlii.edu.au",
        "description": "Australasian Legal Information Institute"
    }
}
