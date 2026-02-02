"""
Analyst Agent - Tracks progress and provides insights
"""
from typing import List, Dict, Any, Optional
from datetime import datetime
from crewai import Agent
from .base_agent import BaseAgent
from models.project import TaskDefinition
from config.settings import TaskStatus


class AnalystAgent(BaseAgent):
    """Analyst that tracks project progress and provides insights"""
    
    def __init__(self):
        super().__init__()
        self.tracked_tasks: Dict[str, TaskDefinition] = {}
        self.metrics: Dict[str, Any] = {}
    
    @property
    def role(self) -> str:
        return "Project Analyst"
    
    @property
    def goal(self) -> str:
        return """
        Track project progress, identify bottlenecks, generate reports,
        and provide actionable insights to improve team performance.
        """
    
    @property
    def backstory(self) -> str:
        return """
        You are an experienced Project Analyst with expertise in software development metrics
        and project management. You excel at:
        
        - Tracking task progress and team velocity
        - Identifying blockers and bottlenecks
        - Generating comprehensive progress reports
        - Providing data-driven recommendations
        - Forecasting project completion dates
        - Analyzing team performance patterns
        
        You use metrics and data to help the team continuously improve their processes
        and deliver high-quality software on time.
        """
    
    @property
    def llm_type(self) -> str:
        return "analyst"
    
    def _setup_tools(self) -> None:
        """Analyst uses custom tracking methods"""
        self._tools = []
    
    def track_task(self, task: TaskDefinition) -> None:
        """Add a task to tracking"""
        self.tracked_tasks[task.id] = task
    
    def update_task_status(
        self,
        task_id: str,
        status: TaskStatus,
        output: Any = None
    ) -> Optional[TaskDefinition]:
        """Update tracked task status"""
        if task_id not in self.tracked_tasks:
            return None
        
        task = self.tracked_tasks[task_id]
        task.status = status
        
        if status == TaskStatus.IN_PROGRESS and not task.started_at:
            task.started_at = datetime.now()
        elif status == TaskStatus.COMPLETED:
            task.completed_at = datetime.now()
            task.output = output
            if task.started_at:
                task.actual_hours = (task.completed_at - task.started_at).total_seconds() / 3600
        
        return task
    
    def get_progress_report(self) -> Dict[str, Any]:
        """Generate progress report"""
        total = len(self.tracked_tasks)
        if total == 0:
            return {
                "total_tasks": 0,
                "completed": 0,
                "in_progress": 0,
                "pending": 0,
                "failed": 0,
                "blocked": 0,
                "completion_percentage": 0.0
            }
        
        status_counts = {status: 0 for status in TaskStatus}
        for task in self.tracked_tasks.values():
            status_counts[task.status] += 1
        
        completed = status_counts[TaskStatus.COMPLETED]
        
        return {
            "total_tasks": total,
            "completed": completed,
            "in_progress": status_counts[TaskStatus.IN_PROGRESS],
            "pending": status_counts[TaskStatus.PENDING],
            "failed": status_counts[TaskStatus.FAILED],
            "blocked": status_counts[TaskStatus.BLOCKED],
            "completion_percentage": (completed / total) * 100
        }
    
    def identify_bottlenecks(self) -> List[Dict[str, Any]]:
        """Identify bottlenecks in the project"""
        bottlenecks = []
        
        for task in self.tracked_tasks.values():
            # Check for overdue tasks
            if task.status == TaskStatus.IN_PROGRESS and task.started_at:
                elapsed = (datetime.now() - task.started_at).total_seconds() / 3600
                if elapsed > task.estimated_hours * 1.5:
                    bottlenecks.append({
                        "task_id": task.id,
                        "task_name": task.name,
                        "type": "overdue",
                        "estimated_hours": task.estimated_hours,
                        "elapsed_hours": elapsed,
                        "delay_percentage": ((elapsed - task.estimated_hours) / task.estimated_hours) * 100
                    })
            
            # Check for blocked tasks
            if task.status == TaskStatus.BLOCKED:
                bottlenecks.append({
                "task_id": task.id,
                    "task_name": task.name,
                    "type": "blocked",
                    "dependencies": task.dependencies,
                    "blocked_since": task.started_at.isoformat() if task.started_at else None
                })
        
        return bottlenecks
    
    def get_team_performance(self) -> Dict[str, Any]:
        """Analyze team performance by assignee"""
        performance = {}
        
        for task in self.tracked_tasks.values():
            assignee = task.assigned_to
            if assignee not in performance:
                performance[assignee] = {
                    "total_tasks": 0,
                    "completed_tasks": 0,
                    "total_estimated_hours": 0,
                    "total_actual_hours": 0,
                    "on_time_completions": 0
                }
            
            performance[assignee]["total_tasks"] += 1
            performance[assignee]["total_estimated_hours"] += task.estimated_hours
            
            if task.status == TaskStatus.COMPLETED:
                performance[assignee]["completed_tasks"] += 1
                if task.actual_hours:
                    performance[assignee]["total_actual_hours"] += task.actual_hours
                    if task.actual_hours <= task.estimated_hours:
                        performance[assignee]["on_time_completions"] += 1
        
        # Calculate efficiency for each assignee
        for assignee, data in performance.items():
            if data["completed_tasks"] > 0:
                data["completion_rate"] = (data["completed_tasks"] / data["total_tasks"]) * 100
                data["on_time_rate"] = (data["on_time_completions"] / data["completed_tasks"]) * 100
                if data["total_actual_hours"] > 0:
                    data["efficiency"] = (data["total_estimated_hours"] / data["total_actual_hours"]) * 100
        
        return performance
    
    def generate_summary_report(self) -> str:
        """Generate a comprehensive summary report"""
        progress = self.get_progress_report()
        bottlenecks = self.identify_bottlenecks()
        performance = self.get_team_performance()
        
        report = f"""
================================================================================
                         PROJECT PROGRESS REPORT
                         Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
================================================================================

📊 OVERALL PROGRESS
-------------------
Total Tasks: {progress['total_tasks']}
Completed: {progress['completed']} ({progress['completion_percentage']:.1f}%)
In Progress: {progress['in_progress']}
Pending: {progress['pending']}
Blocked: {progress['blocked']}
Failed: {progress['failed']}

"""
        
        if bottlenecks:
            report += "⚠️  BOTTLENECKS IDENTIFIED\n"
            report += "-" * 25 + "\n"
            for bottleneck in bottlenecks:
                report += f"  - {bottleneck['task_name']} ({bottleneck['type']})\n"
            report += "\n"
        
        if performance:
            report += "👥 TEAM PERFORMANCE\n"
            report += "-" * 25 + "\n"
            for assignee, data in performance.items():
                report += f"  {assignee}:\n"
                report += f"    Tasks: {data['completed_tasks']}/{data['total_tasks']} completed\n"
                if 'completion_rate' in data:
                    report += f"    Completion Rate: {data['completion_rate']:.1f}%\n"
                if 'on_time_rate' in data:
                    report += f"    On-Time Rate: {data['on_time_rate']:.1f}%\n"
            report += "\n"
        
        report += "=" * 80 + "\n"
        
        return report
