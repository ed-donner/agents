from pydantic import BaseModel, Field
from typing import List

class Doctor(BaseModel):
    file_name: str = Field(description="The exact name of the .md file (e.g., 'doctor_GregoryHouse_Neurology.md')")
    doctor_name: str = Field(description="The full name of the doctor extracted from the file or content")
    movie: str = Field(description ="Movie title to which doctor belongs to")
    speciality: str = Field(description="The medical field of expertise for this specific doctor")
    diagnosis: str = Field(description="The full text of the diagnosis as copied verbatim from the .md file produced by this doctor")
    @property
    def diagnosis_info(self) -> str:
        return f"This diagnosis comes verbatim from {self.file_name} produced by {self.doctor_name}"

class Doctors(BaseModel):
    doctors: List[Doctor] = Field(description = "List of doctors recruited for diagnose based on given symptoms")

class DiagnosisEvaluation(BaseModel):
    """Evaluation details for an individual doctor's diagnosis."""
    doctor: Doctor = Field(description = "doctor under evaluation")
    strengths: List[str] = Field(description="A list of positive aspects or accurate clinical findings in this diagnosis")
    weaknesses: List[str] = Field(description="A list of missing information, errors, or areas for improvement")
    score: int = Field(ge=1, le=10, description="An overall quality score from 1 (poor) to 10 (excellent)")

class ChosenDiagnosis(BaseModel):
    """The final selection of the best diagnosis among all candidates."""
    doctor: Doctor = Field(description="Winning doctor")
    evaluation: DiagnosisEvaluation = Field(description="Evaluation of winning doctor")

class EvaluatorResponse(BaseModel):
    """The final structured output containing all evaluations and the final decision."""
    evaluations: List[DiagnosisEvaluation] = Field(description="A list containing an evaluation for every file processed")
    chosen: ChosenDiagnosis = Field(description="The specific diagnosis selected as the most accurate and comprehensive")