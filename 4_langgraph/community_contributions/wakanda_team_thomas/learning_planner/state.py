"""
State definitions and Pydantic models for the Learning Path Generator.
"""

from typing import Annotated, Optional, List, Any
from typing_extensions import TypedDict
from langgraph.graph.message import add_messages
from pydantic import BaseModel, Field


class LearningResource(BaseModel):
    """A single learning resource (article, video, course, etc.)"""
    title: str = Field(description="A clear and concise title of the resource")
    url: str = Field(description="URL to access the resource")
    type: str = Field(description="Type: article, video, course, book, docs, tutorial")
    difficulty: str = Field(description="Difficulty: beginner, intermediate, advanced, expert")
    estimated_time: Optional[str] = Field(default=None, description="Estimated time to complete in minutes")


class Milestone(BaseModel):
    """A phase/milestone in the learning path"""
    phase_number: int = Field(description="Phase number in sequence")
    title: str = Field(description="A clear and concise title of this phase")
    goal: str = Field(description="What the learner will achieve in this phase")
    description: str = Field(description="A detailed description of this phase")
    resources: List[LearningResource] = Field(description="Learning resources for this phase")
    project_idea: Optional[str] = Field(default=None, description="Hands-on project suggestion")
    estimated_days: int = Field(description="Estimated days to complete this phase in days")


class CurriculumOutput(BaseModel):
    """Structured output from the Curriculum Builder"""
    overview: str = Field(description="A brief overview of the learning path")
    total_estimated_days: int = Field(description="Total estimated days to complete")
    milestones: List[Milestone] = Field(description="Ordered list of learning milestones")


class EvaluatorOutput(BaseModel):
    """Structured output from the Evaluator"""
    feedback: str = Field(description="A detailed feedback on the curriculum")
    is_complete: bool = Field(description="Whether the curriculum meets all criteria")
    needs_user_input: bool = Field(description="Whether user clarification is needed to improve the curriculum")
    issues: Optional[List[str]] = Field(default=None, description="List of specific issues to address")


class State(TypedDict):
    """Main state for the Learning Path Generator graph"""
    # Conversation history (uses add_messages reducer)
    messages: Annotated[List[Any], add_messages]
    
    # User inputs
    topic: str = Field(description="The topic of the learning path")
    user_email: str = Field(description="The email of the user")
    current_skill_level: str = Field(description="The current skill level of the user: none, beginner, intermediate, advanced, expert")
    time_commitment: str = Field(description="The time commitment of the user: 30min/day, 1hr/day, 2hr/day, weekends")
    
    # Research outputs
    prerequisites: Optional[List[str]] = Field(default=None, description="A list of prerequisites for the learning path")
    key_concepts: Optional[List[str]] = Field(default=None, description="A list of key concepts for the learning path")
    research_summary: Optional[str] = Field(default=None, description="A summary of the research done on the topic")
    
    # Curriculum outputs
    curriculum: Optional[CurriculumOutput] = Field(default=None, description="The curriculum for the learning path")
    
    # Evaluator outputs
    evaluation_feedback: Optional[str] = Field(default=None, description="A feedback on the curriculum")
    is_complete: bool = Field(description="Whether the curriculum is complete")
    needs_user_input: bool = Field(description="Whether user clarification is needed to improve the curriculum")
    revision_count: int = Field(description="Number of revision iterations")
    
    # Writer outputs
    markdown_content: Optional[str] = Field(default=None, description="The markdown content of the learning path")
    markdown_path: Optional[str] = Field(default=None, description="The path to the markdown file")
    pdf_path: Optional[str] = Field(default=None, description="The path to the pdf file")
    
    # Notifier outputs
    notification_status: Optional[str] = Field(default=None, description="The status of the notification")
    notification_sent: bool = Field(description="Whether the notification has been sent")
