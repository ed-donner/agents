from typing import Optional, List, Tuple
from pydantic import BaseModel, Field
from enum import Enum
import re
from agents import Agent, Runner, input_guardrail, output_guardrail, GuardrailFunctionOutput
from model_config import mimo_model


class QueryValidationResult(BaseModel):
    """Result of query validation"""
    is_valid: bool
    error_message: Optional[str] = None
    sanitized_query: Optional[str] = None
    warning_message: Optional[str] = None
    query_category: Optional[str] = None


class ReportValidationResult(BaseModel):
    """Result of report validation"""
    is_valid: bool
    error_message: Optional[str] = None
    needs_disclaimer: bool = False
    query_category: Optional[str] = None


class QueryCategory(str, Enum):
    """Categories of research queries"""
    ACADEMIC = "academic"
    BUSINESS = "business"
    TECHNICAL = "technical"
    GENERAL = "general"
    SENSITIVE = "sensitive"
    INAPPROPRIATE = "inappropriate"


# Input Validation Agent
input_validation_agent = Agent(
    name="InputValidator",
    instructions="""You are an input validation specialist. Check if the research query is appropriate and safe.
    
    Validate for:
    - Minimum length (3 characters)
    - Maximum length (500 characters)
    - No harmful content (hacking, weapons, illegal activities)
    - Identify if topic is sensitive (medical, legal, financial advice)
    
    Return a JSON object with these exact fields:
    - is_valid (boolean): true if query passes validation, false otherwise
    - error_message (string or null): error message if is_valid is false, null otherwise
    - sanitized_query (string or null): cleaned up version of the query
    - warning_message (string or null): warning if sensitive topic
    - query_category (string or null): ACADEMIC, BUSINESS, TECHNICAL, GENERAL, SENSITIVE, or INAPPROPRIATE
    """,
    output_type=QueryValidationResult,
    model=mimo_model
)

# Output Validation Agent
output_validation_agent = Agent(
    name="OutputValidator",
    instructions="""You are a report validation specialist. Check if the research report meets quality standards.
    
    Validate for:
    - Minimum length (100 characters)
    - Maximum length (50000 characters)
    - Content completeness
    - Determine if disclaimer needed based on topic sensitivity
    
    Return a JSON object with these exact fields:
    - is_valid (boolean): true if report passes validation, false otherwise
    - error_message (string or null): error message if is_valid is false, null otherwise
    - needs_disclaimer (boolean): true if disclaimer should be added
    - query_category (string or null): category of the topic
    """,
    output_type=ReportValidationResult,
    model=mimo_model
)


@input_guardrail
async def validate_research_input(ctx, agent, message):
    """Input guardrail for research queries"""
    result = await Runner.run(input_validation_agent, message, context=ctx.context)
    validation = result.final_output
    
    return GuardrailFunctionOutput(
        output_info={"validation": validation},
        tripwire_triggered=not validation.is_valid
    )


@output_guardrail
async def validate_research_output(ctx, agent, output):
    """Output guardrail for research reports"""
    # Extract the report text from output
    report_text = str(output)
    
    result = await Runner.run(output_validation_agent, f"Validate this report:\n\n{report_text[:1000]}", context=ctx.context)
    validation = result.final_output
    
    # Add disclaimer if needed
    if validation.is_valid and validation.needs_disclaimer:
        disclaimer = get_disclaimer(validation.query_category)
        # Modify output to include disclaimer
        return GuardrailFunctionOutput(
            output_info={"validation": validation, "added_disclaimer": True},
            tripwire_triggered=False
        )
    
    return GuardrailFunctionOutput(
        output_info={"validation": validation},
        tripwire_triggered=not validation.is_valid
    )


def get_disclaimer(category: Optional[str]) -> str:
    """Get appropriate disclaimer for category"""
    disclaimers = {
        "SENSITIVE": (
            "\n\n---\n**DISCLAIMER**: This report is for informational purposes only "
            "and does not constitute professional medical, legal, or financial advice. "
            "Please consult qualified professionals for specific guidance.\n---\n"
        ),
        "GENERAL": (
            "\n\n---\n**Note**: This research report is generated using AI and web sources. "
            "Please verify critical information with authoritative sources.\n---\n"
        )
    }
    return disclaimers.get(category, disclaimers["GENERAL"])


class RateLimitGuard:
    """Rate limiting for API calls"""
    
    def __init__(self, max_queries_per_hour: int = 10):
        self.max_queries_per_hour = max_queries_per_hour
        self.query_timestamps: List[float] = []
    
    def can_process_query(self) -> Tuple[bool, Optional[str]]:
        """Check if query can be processed based on rate limits"""
        import time
        current_time = time.time()
        
        self.query_timestamps = [
            ts for ts in self.query_timestamps 
            if current_time - ts < 3600
        ]
        
        if len(self.query_timestamps) >= self.max_queries_per_hour:
            return False, f"Rate limit exceeded. Maximum {self.max_queries_per_hour} queries per hour."
        
        self.query_timestamps.append(current_time)
        return True, None
