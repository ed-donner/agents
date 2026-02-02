"""
Analysis Crew - For requirement analysis and architecture design only
"""
from typing import Dict, Any, Optional
from crewai import Crew, Process
from loguru import logger

from agents import TeamManagerAgent, AnalystAgent
from tasks import AnalysisTasks
from models.requirements import ComplexStackRequest
from config.settings import settings


class AnalysisCrew:
    """
    Lighter crew for analysis phase only
    """
    
    def __init__(self, request: ComplexStackRequest):
        self.request = request
        self.manager = TeamManagerAgent()
        self.analyst = AnalystAgent()
        self.crew: Optional[Crew] = None
        
        logger.info(f"Initialized AnalysisCrew for: {request.project_name}")
    
    def build_crew(self) -> Crew:
        """Build analysis crew"""
        
        # Create analysis tasks
        requirement_task = AnalysisTasks.requirement_analysis(
            agent=self.manager.get_agent(),
            request=self.request
        )
        
        architecture_task = AnalysisTasks.architecture_design(
            agent=self.manager.get_agent(),
            request=self.request,
            context=[requirement_task]
        )
        
        decomposition_task = AnalysisTasks.task_decomposition(
            agent=self.manager.get_agent(),
            request=self.request,
            context=[requirement_task, architecture_task]
        )
        
        self.crew = Crew(
            agents=[
                self.manager.get_agent(),
                self.analyst.get_agent()
            ],
            tasks=[
                requirement_task,
                architecture_task,
                decomposition_task
            ],
            process=Process.sequential,
            verbose=settings.crewai_verbose
        )
        
        return self.crew
    
    def run(self) -> Dict[str, Any]:
        """Run analysis"""
        if not self.crew:
            self.build_crew()
        
        logger.info("Running analysis...")
        
        try:
            result = self.crew.kickoff()
            return {
                "status": "success",
                "analysis": result
            }
        except Exception as e:
            logger.error(f"Analysis failed: {e}")
            return {
                "status": "error",
                "error": str(e)
            }
