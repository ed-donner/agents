"""
Resume Parser Agent.

Extracts structured information from resume documents (PDF/DOCX).
"""

from typing import Optional
from pydantic import BaseModel, Field

from agents import Agent, function_tool

from src.utils.extractors import extract_text, is_supported_file, ExtractionError


class ParsedSkill(BaseModel):
    """A skill extracted from resume."""
    name: str = Field(description="Name of the skill")
    level: Optional[str] = Field(
        default=None,
        description="Proficiency level: beginner, intermediate, advanced, or expert"
    )
    years: Optional[int] = Field(
        default=None,
        description="Years of experience with this skill, if mentioned"
    )


class ParsedExperience(BaseModel):
    """Work experience extracted from resume."""
    company: str = Field(description="Company or organization name")
    title: str = Field(description="Job title or position")
    start_date: Optional[str] = Field(
        default=None,
        description="Start date in format YYYY-MM or YYYY"
    )
    end_date: Optional[str] = Field(
        default=None,
        description="End date in format YYYY-MM or YYYY, or 'Present' if current"
    )
    description: Optional[str] = Field(
        default=None,
        description="Brief description of responsibilities and achievements"
    )
    location: Optional[str] = Field(
        default=None,
        description="Location of the job, if mentioned"
    )


class ParsedEducation(BaseModel):
    """Education entry extracted from resume."""
    institution: str = Field(description="Name of school, university, or institution")
    degree: Optional[str] = Field(
        default=None,
        description="Degree obtained (e.g., Bachelor's, Master's, PhD)"
    )
    field: Optional[str] = Field(
        default=None,
        description="Field of study or major"
    )
    graduation_date: Optional[str] = Field(
        default=None,
        description="Graduation date in format YYYY-MM or YYYY"
    )


class ParsedResume(BaseModel):
    """Structured resume data extracted by the parser agent."""
    name: str = Field(description="Full name of the candidate")
    email: Optional[str] = Field(
        default=None,
        description="Email address"
    )
    phone: Optional[str] = Field(
        default=None,
        description="Phone number"
    )
    location: Optional[str] = Field(
        default=None,
        description="Location or address"
    )
    summary: Optional[str] = Field(
        default=None,
        description="Professional summary or objective statement"
    )
    skills: list[ParsedSkill] = Field(
        default_factory=list,
        description="List of technical and professional skills"
    )
    experience: list[ParsedExperience] = Field(
        default_factory=list,
        description="List of work experiences, most recent first"
    )
    education: list[ParsedEducation] = Field(
        default_factory=list,
        description="List of education entries"
    )
    certifications: list[str] = Field(
        default_factory=list,
        description="List of certifications or licenses"
    )
    languages: list[str] = Field(
        default_factory=list,
        description="List of spoken/written languages"
    )
    keywords: list[str] = Field(
        default_factory=list,
        description="Key terms and technologies from the resume for job matching"
    )


def _extract_resume_text_impl(file_path: str) -> str:
    """
    Extract text content from a resume file.
    
    Args:
        file_path: Path to the resume file (PDF or DOCX format)
        
    Returns:
        The extracted text content from the resume
    """
    if not is_supported_file(file_path):
        return f"Error: Unsupported file format. Please provide a PDF or DOCX file."
    
    try:
        text = extract_text(file_path)
        if not text.strip():
            return "Error: The file appears to be empty or could not be read."
        return text
    except ExtractionError as e:
        return f"Error extracting text: {str(e)}"
    except Exception as e:
        return f"Error: {str(e)}"


@function_tool
def extract_resume_text(file_path: str) -> str:
    """
    Extract text content from a resume file.
    
    Args:
        file_path: Path to the resume file (PDF or DOCX format)
        
    Returns:
        The extracted text content from the resume
    """
    return _extract_resume_text_impl(file_path)


PARSER_INSTRUCTIONS = """You are a professional resume parser. Your task is to extract 
structured information from resume text.

When parsing a resume:

1. Extract the candidate's name, contact information (email, phone, location)
2. Identify the professional summary or objective if present
3. Extract all skills mentioned, inferring proficiency levels when possible:
   - "expert" or "advanced" for skills with 5+ years or explicitly stated expertise
   - "intermediate" for skills with 2-5 years or regular use mentioned
   - "beginner" for skills recently learned or with limited experience
4. Extract work experience in reverse chronological order:
   - Company name and job title are required
   - Include dates when available (use YYYY-MM format)
   - Summarize key responsibilities and achievements
5. Extract education information including institution, degree, and field
6. List any certifications or professional licenses
7. Note any languages spoken
8. Generate a list of keywords for job matching (technologies, methodologies, domains)

Be thorough but accurate. Only include information that is actually present in the resume.
If information is unclear or ambiguous, make reasonable inferences but avoid fabrication.

IMPORTANT: First use the extract_resume_text tool to get the text content from the file,
then parse that text into the structured format."""


resume_parser_agent = Agent(
    name="ResumeParserAgent",
    instructions=PARSER_INSTRUCTIONS,
    model="gpt-4o-mini",
    tools=[extract_resume_text],
    output_type=ParsedResume,
)


async def parse_resume(file_path: str) -> ParsedResume:
    """
    Parse a resume file and extract structured information.
    
    Args:
        file_path: Path to the resume file (PDF or DOCX)
        
    Returns:
        ParsedResume with extracted information
        
    Raises:
        ExtractionError: If the file cannot be read
        ValueError: If parsing fails
    """
    from agents import Runner
    
    result = await Runner.run(
        resume_parser_agent,
        f"Parse the resume at: {file_path}",
    )
    
    return result.final_output_as(ParsedResume)
