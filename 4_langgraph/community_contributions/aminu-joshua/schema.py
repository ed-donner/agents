from pydantic import BaseModel, Field

class CoverLetterData(BaseModel):
    cover_letter: str = Field(description="The cover letter for the candidate")
    role: str = Field(description="The role of the candidate")
    hiring_manager_email: str = Field(description="The email of the hiring manager")
    hiring_manager_name: str = Field(description="The name of the hiring manager")
    company: str = Field(description="The company the candidate is applying to")

class ResumeData(BaseModel):
    cover_letter_data: CoverLetterData = Field(description="Cover letter data")
    resume_path: str = Field(description="The path to the resume file")
