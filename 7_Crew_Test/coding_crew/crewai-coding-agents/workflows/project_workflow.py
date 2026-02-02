"""
Project Workflow - Orchestrates the complete project lifecycle
"""
from typing import Dict, Any, Optional, Callable
from datetime import datetime
from loguru import logger
import json
import os

from models.requirements import ComplexStackRequest
from models.project import Project
from crews import DevelopmentCrew, AnalysisCrew
from config.settings import settings


class ProjectWorkflow:
    """
    Manages the complete project development workflow
    """
    
    def __init__(
        self,
        request: ComplexStackRequest,
        output_dir: Optional[str] = None,
        on_progress: Optional[Callable[[Dict], None]] = None
    ):
        self.request = request
        self.output_dir = output_dir or os.path.join(settings.output_dir, request.project_name)
        self.on_progress = on_progress
        
        self.project = Project(
            name=request.project_name,
            description=request.description
        )
        
        self.phases = {
            "analysis": {"status": "pending", "result": None},
            "development": {"status": "pending", "result": None},
            "review": {"status": "pending", "result": None}
        }
        
        # Ensure output directory exists
        os.makedirs(self.output_dir, exist_ok=True)
        
        logger.info(f"Initialized ProjectWorkflow: {request.project_name}")
    
    def _emit_progress(self, phase: str, status: str, data: Any = None):
        """Emit progress update"""
        progress = {
            "timestamp": datetime.now().isoformat(),
            "phase": phase,
            "status": status,
            "data": data,
            "overall_progress": self._calculate_progress()
        }
        
        if self.on_progress:
            self.on_progress(progress)
        
        logger.info(f"Progress: {phase} - {status}")
    
    def _calculate_progress(self) -> float:
        """Calculate overall progress percentage"""
        completed = sum(1 for p in self.phases.values() if p["status"] == "completed")
        return (completed / len(self.phases)) * 100
    
    def run_analysis_only(self) -> Dict[str, Any]:
        """Run only the analysis phase"""
        logger.info("Running analysis phase only...")
        
        self._emit_progress("analysis", "started")
        
        try:
            analysis_crew = AnalysisCrew(self.request)
            result = analysis_crew.run()
            
            self.phases["analysis"]["status"] = "completed"
            self.phases["analysis"]["result"] = result
            
            # Save analysis results
            self._save_output("analysis", result)
            
            self._emit_progress("analysis", "completed", result)
            
            return result
            
        except Exception as e:
            logger.error(f"Analysis phase failed: {e}")
            self.phases["analysis"]["status"] = "failed"
            self._emit_progress("analysis", "failed", str(e))
            raise
    
    def run_full_development(self) -> Dict[str, Any]:
        """Run the complete development workflow"""
        logger.info("Starting full development workflow...")
        
        results = {}
        
        # Phase 1: Analysis
        self._emit_progress("analysis", "started")
        try:
            analysis_crew = AnalysisCrew(self.request)
            analysis_result = analysis_crew.run()
            
            self.phases["analysis"]["status"] = "completed"
            self.phases["analysis"]["result"] = analysis_result
            results["analysis"] = analysis_result
            
            self._save_output("analysis", analysis_result)
            self._emit_progress("analysis", "completed", analysis_result)
            
        except Exception as e:
            logger.error(f"Analysis failed: {e}")
            self.phases["analysis"]["status"] = "failed"
            self._emit_progress("analysis", "failed", str(e))
            raise
        
        # Phase 2: Development
        self._emit_progress("development", "started")
        try:
            dev_crew = DevelopmentCrew(self.request)
            dev_result = dev_crew.run()
            
            self.phases["development"]["status"] = "completed"
            self.phases["development"]["result"] = dev_result
            results["development"] = dev_result
            
            self._save_output("development", dev_result)
            self._emit_progress("development", "completed", dev_result)
            
        except Exception as e:
            logger.error(f"Development failed: {e}")
            self.phases["development"]["status"] = "failed"
            self._emit_progress("development", "failed", str(e))
            raise
        
        # Phase 3: Review
        self._emit_progress("review", "started")
        try:
            review_result = self._run_review(results)
            
            self.phases["review"]["status"] = "completed"
            self.phases["review"]["result"] = review_result
            results["review"] = review_result
            
            self._save_output("review", review_result)
            self._emit_progress("review", "completed", review_result)
            
        except Exception as e:
            logger.error(f"Review failed: {e}")
            self.phases["review"]["status"] = "failed"
            self._emit_progress("review", "failed", str(e))
            raise
        
        # Final summary
        results["summary"] = self._generate_summary(results)
        self._save_output("summary", results["summary"])
        
        logger.info("Full development workflow completed")
        
        return results
    
    def _run_review(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Run review phase (placeholder for actual review logic)"""
        return {
            "status": "completed",
            "findings": [],
            "recommendations": [],
            "approval": True
        }
    
    def _generate_summary(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate project summary"""
        return {
            "project_name": self.request.project_name,
            "completed_at": datetime.now().isoformat(),
            "phases_completed": len([p for p in self.phases.values() if p["status"] == "completed"]),
            "total_phases": len(self.phases),
            "output_directory": self.output_dir
        }
    
    def _save_output(self, phase: str, data: Any):
        """Save phase output to file"""
        output_file = os.path.join(self.output_dir, f"{phase}_output.json")
        
        try:
            with open(output_file, 'w') as f:
                json.dump(data, f, indent=2, default=str)
            logger.info(f"Saved {phase} output to {output_file}")
        except Exception as e:
            logger.error(f"Failed to save {phase} output: {e}")
    
    def get_status(self) -> Dict[str, Any]:
        """Get current workflow status"""
        return {
            "project": self.project.model_dump(),
            "phases": self.phases,
            "progress": self._calculate_progress()
        }
