from pydantic import BaseModel, Field

class ClarifyingQuestions(BaseModel):
  question: str = Field(description="")
  reason: str = Field(description="")


class ResearchManagerUpdates(BaseModel):
  clarifying_questions: list[ClarifyingQuestions] = Field(description="A list of clarifying questions")
  status: str = Field(description="Updates about current_step being performed and status update if the step is completed")
  current_step: str = Field(description="Information about the current step that is being performed")
  is_completed: bool = Field(description="True or False if all the tasks are completed")
  report: str = Field(description="The final report")
  error: str = Field(description="any error encountered")

class EvaluationModel(BaseModel):
  is_satisfied: bool
  feedback: str


class Clarification(BaseModel):
  clarifying_questions: list[ClarifyingQuestions] = Field(description="A list of clarifying questions")

class WebSearchTerm(BaseModel):
  reason: str = Field(description="")
  search_term: str = Field(description="")
  clarifying_questions: list[ClarifyingQuestions] = Field(description="A list of clarifying questions ")

class WebSearchPlan(BaseModel):
  searches: list[WebSearchTerm] = Field(description="A list of web searches to perform to best answer the query")

class ReportData(BaseModel):
    short_summary: str = Field(description="A short 2-3 sentence summary of the findings.")

    markdown_report: str = Field(description="The final report")

    follow_up_questions: list[str] = Field(description="Suggested topics to research further")