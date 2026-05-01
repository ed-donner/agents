"""
Bio Agent — Tool Definitions
------------------------------
Bridges the LLM and the data layers.
Contains: wrapper functions, JSON schemas, and a tool registry.
"""

import json

import database
import rag


# ═══════════════════════════════════════════════════════════════════════
#  TOOL WRAPPER FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════

def search_knowledge_base(query: str) -> str:
    """Search the knowledge base for relevant information."""
    return rag.search_knowledge_base(query)


def lookup_faq(question: str) -> str:
    """Check if this question has a cached high-quality answer."""
    answer = database.lookup_faq(question)
    if answer:
        return json.dumps({"found": True, "answer": answer})
    return json.dumps({"found": False, "message": "No FAQ match found."})


def record_contact(email: str, name: str = "", notes: str = "") -> str:
    """Record a user's contact information."""
    database.save_contact(email=email, name=name, notes=notes)
    return json.dumps({"recorded": True, "email": email})


# ═══════════════════════════════════════════════════════════════════════
#  JSON SCHEMAS (OpenAI tool-calling format)
# ═══════════════════════════════════════════════════════════════════════

search_knowledge_base_schema = {
    "name": "search_knowledge_base",
    "description": "Search the knowledge base for facts about the person's career, skills, and experience.",
    "parameters": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "What to search for",
            }
        },
        "required": ["query"],
        "additionalProperties": False,
    },
}

lookup_faq_schema = {
    "name": "lookup_faq",
    "description": "Check if this question was answered before. Call this FIRST before searching the knowledge base.",
    "parameters": {
        "type": "object",
        "properties": {
            "question": {
                "type": "string",
                "description": "The question to look up",
            }
        },
        "required": ["question"],
        "additionalProperties": False,
    },
}

record_contact_schema = {
    "name": "record_contact",
    "description": "Save a user's contact info when they share their email.",
    "parameters": {
        "type": "object",
        "properties": {
            "email": {
                "type": "string",
                "description": "Email address",
            },
            "name": {
                "type": "string",
                "description": "Name if provided",
            },
            "notes": {
                "type": "string",
                "description": "Extra context",
            },
        },
        "required": ["email"],
        "additionalProperties": False,
    },
}


# ═══════════════════════════════════════════════════════════════════════
#  REGISTRY
# ═══════════════════════════════════════════════════════════════════════

# For the OpenAI API tools parameter
TOOLS_LIST = [
    {"type": "function", "function": search_knowledge_base_schema},
    {"type": "function", "function": lookup_faq_schema},
    {"type": "function", "function": record_contact_schema},
]

# For dispatching tool calls by name
TOOLS_MAP: dict[str, callable] = {
    "search_knowledge_base": search_knowledge_base,
    "lookup_faq": lookup_faq,
    "record_contact": record_contact,
}
