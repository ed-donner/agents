"""
Code Engineer Agent
Responsibility: Generate production-quality Python code implementing the
discharge summary generation logic for the hospital's system.
"""

from src.utils.llm_client import call_llm

SYSTEM_PROMPT = """You are a senior Python software engineer specializing in 
healthcare information systems.

Given a complete, reviewed discharge summary and its underlying patient data,
generate a clean Python module that:
1. Defines a PatientData dataclass with all relevant fields
2. Implements a DischargeSummaryGenerator class with a generate() method
3. Includes a sample usage example with realistic patient data
4. Follows PEP 8, uses type hints throughout
5. Includes docstrings for all public classes and methods
6. Is ready to integrate with an EMR (Electronic Medical Record) system

Format each file as:

```python filename: discharge_generator.py
# ... code ...
```

```python filename: patient_models.py
# ... code ...
```

```python filename: example_usage.py
# ... code ...
```

Keep code clean, professional, and free of placeholders.
"""


def run(patient_json: str, discharge_summary: str, qa_report: str) -> str:
    """
    Generate production Python code for the discharge summary system.
    Returns code blocks as formatted text.
    """
    prompt = (
        f"PATIENT DATA STRUCTURE:\n{patient_json}\n\n"
        f"DISCHARGE SUMMARY EXAMPLE:\n{discharge_summary}\n\n"
        f"QA REQUIREMENTS (from review):\n{qa_report}\n\n"
        "Generate the complete Python implementation."
    )
    return call_llm(
        system_prompt=SYSTEM_PROMPT,
        user_prompt=prompt,
        temperature=0.3,
    )
