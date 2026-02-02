"""
Project and task models
"""
from typing import Dict, List, Optional, Any
from datetime import datetime
from pydantic import BaseModel, Field
import uuid

from config.settings import TaskStatus, TaskPriority


class TaskDefinition(BaseModel):
    """Task definition for agent execution"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str
    assigned_to: str
    priority: TaskPriority = TaskPriority.MEDIUM
    status: TaskStatus = TaskStatus.PENDING
    dependencies: List[str] = Field(default_factory=list)
    estimated_hours: float = 1.0
    actual_hours: Optional[float] = None
    output: Optional[Any] = None
    error: Optional[str] = None
    callbacks: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    class Config:
        use_enum_values = True


class ServiceDefinition(BaseModel):
    """Microservice definition"""
    name: str
    description: str
    language: str
    framework: str
    port: int
    endpoints: List[Dict[str, Any]] = Field(default_factory=list)
    dependencies: List[str] = Field(default_factory=list)
    database: Optional[str] = None
    cache: Optional[str] = None


class ProjectArchitecture(BaseModel):
    """Project architecture definition"""
    pattern: str = "monolith"  # monolith, microservices, modular_monolith
    services: List[ServiceDefinition] = Field(default_factory=list)
    api_gateway: Optional[str] = None
    service_mesh: Optional[str] = None
    event_bus: Optional[str] = None
    diagram: Optional[str] = None


class Project(BaseModel):
    """Complete project definition"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str
    status: str = "pending"
    architecture: Optional[ProjectArchitecture] = None
    tasks: List[TaskDefinition] = Field(default_factory=list)
    generated_files: Dict[str, str] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    
    def add_task(self, task: TaskDefinition):
        """Add a task to the project"""
        self.tasks.append(task)
        self.updated_at = datetime.now()
    
    def get_task(self, task_id: str) -> Optional[TaskDefinition]:
        """Get task by ID"""
        for task in self.tasks:
            if task.id == task_id:
                return task
        return None
    
    def update_task_status(self, task_id: str, status: TaskStatus, output: Any = None):
        """Update task status"""
        task = self.get_task(task_id)
        if task:
            task.status = status
            if status == TaskStatus.IN_PROGRESS and not task.started_at:
                task.started_at = datetime.now()
            elif status == TaskStatus.COMPLETED:
                task.completed_at = datetime.now()
                task.output = output
            self.updated_at = datetime.now()
    
    def get_progress(self) -> Dict[str, Any]:
        """Calculate project progress"""
        total = len(self.tasks)
        if total == 0:
            return {"total": 0, "completed": 0, "percentage": 0}
        
        completed = sum(1 for t in self.tasks if t.status == TaskStatus.COMPLETED)
        in_progress = sum(1 for t in self.tasks if t.status == TaskStatus.IN_PROGRESS)
        failed = sum(1 for t in self.tasks if t.status == TaskStatus.FAILED)
        blocked = sum(1 for t in self.tasks if t.status == TaskStatus.BLOCKED)
        
        return {
            "total": total,
            "completed": completed,
            "in_progress": in_progress,
            "failed": failed,
            "blocked": blocked,
            "pending": total - completed - in_progress - failed - blocked,
            "percentage": round((completed / total) * 100, 2)
        }
