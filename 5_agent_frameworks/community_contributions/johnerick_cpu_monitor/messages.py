from pydantic import BaseModel, Field


class MonitorRequest(BaseModel):
    pass  


class MetricsReport(BaseModel):
    raw_output: str = Field(description="Raw shell output from monitoring", min_length=1)


class TriageReport(BaseModel):
    raw_output: str = Field(description="Raw shell output from monitoring")
    severity: str = Field(description="Severity of the incident | low | medium | high | critical")
    summary: str = Field(description="Summary of the incident")
    suggested_action: str = Field(description="Suggested action to take")


class FixerRequest(BaseModel):
    triage: TriageReport = Field(description="Triage report of the incident")
    approved: bool = Field(description="True if the incident is approved, False otherwise")


class IncidentResult(BaseModel):
    severity: str = Field(description="Severity of the incident")
    action_taken: str = Field(description="Action taken to fix the incident")
    outcome: str = Field(description="Outcome of the incident")
