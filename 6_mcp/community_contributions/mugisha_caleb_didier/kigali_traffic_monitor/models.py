from pydantic import BaseModel, Field
from enum import Enum


class CongestionLevel(str, Enum):
    FREE_FLOW = "free_flow"
    LIGHT = "light"
    MODERATE = "moderate"
    HEAVY = "heavy"


class SegmentStatus(BaseModel):
    segment_id: str = Field(description="The road segment identifier")
    segment_name: str = Field(description="Human-readable road name")
    live_travel_time_secs: int = Field(description="Travel time with current traffic in seconds")
    base_travel_time_secs: int = Field(description="Travel time without traffic in seconds")
    delay_seconds: int = Field(description="Additional delay compared to baseline, in seconds")
    delay_minutes: float = Field(description="Delay in minutes")
    congestion_ratio: float = Field(description="Ratio of live to baseline travel time, e.g. 1.3 means 30% slower")
    congestion_level: CongestionLevel = Field(description="Congestion classification")


class Incident(BaseModel):
    description: str = Field(description="What happened")
    road: str = Field(default="", description="Road name or number if available")
    severity: str = Field(description="Minor, Moderate, Major, or Unknown")
    delay_seconds: int = Field(default=0, description="Delay caused in seconds")


class TrafficReport(BaseModel):
    summary: str = Field(description="2-3 sentence overall traffic summary for Kigali right now")
    segments: list[SegmentStatus] = Field(description="Status for each monitored road segment")
    incidents: list[Incident] = Field(default_factory=list, description="Active traffic incidents in Kigali")
    checked_at: str = Field(description="ISO timestamp of when the check was performed")
