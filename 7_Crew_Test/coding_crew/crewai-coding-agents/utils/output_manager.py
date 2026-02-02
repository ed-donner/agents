"""
Output Manager - Saves crew execution results
"""
import os
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict


class OutputManager:
    """Manages output artifacts from crew executions"""
    
    def __init__(self, base_output_dir: str = "./output"):
        self.base_output_dir = Path(base_output_dir)
        self.base_output_dir.mkdir(exist_ok=True)
    
    def create_project_output(self, project_name: str) -> Path:
        """Create a new output directory for a project"""
        # Sanitize project name
        safe_name = "".join(c if c.isalnum() or c in ('-', '_') else '_' for c in project_name)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        project_dir = self.base_output_dir / f"{safe_name}_{timestamp}"
        
        # Create directory structure
        (project_dir / "analysis").mkdir(parents=True, exist_ok=True)
        (project_dir / "architecture").mkdir(parents=True, exist_ok=True)
        (project_dir / "tasks").mkdir(parents=True, exist_ok=True)
        (project_dir / "generated_code").mkdir(parents=True, exist_ok=True)
        (project_dir / "infrastructure").mkdir(parents=True, exist_ok=True)
        (project_dir / "documentation").mkdir(parents=True, exist_ok=True)
        (project_dir / "reports").mkdir(parents=True, exist_ok=True)
        
        return project_dir
    
    def save_analysis_result(self, project_dir: Path, result: Any):
        """Save analysis crew results"""
        output_file = project_dir / "analysis" / "analysis_report.md"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            if isinstance(result, dict):
                f.write(f"# Project Analysis Report\n\n")
                f.write(f"**Generated:** {datetime.now().isoformat()}\n\n")
                
                for key, value in result.items():
                    f.write(f"## {key}\n\n")
                    f.write(f"{value}\n\n")
            else:
                f.write(str(result))
        
        print(f"✅ Analysis saved to: {output_file}")
        return output_file
    
    def save_architecture(self, project_dir: Path, architecture: Dict):
        """Save architecture design"""
        output_file = project_dir / "architecture" / "architecture_design.md"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(f"# System Architecture Design\n\n")
            f.write(f"**Generated:** {datetime.now().isoformat()}\n\n")
            f.write(json.dumps(architecture, indent=2))
        
        print(f"✅ Architecture saved to: {output_file}")
        return output_file
    
    def save_task_breakdown(self, project_dir: Path, tasks: Any):
        """Save task breakdown"""
        output_file = project_dir / "tasks" / "task_breakdown.md"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(f"# Project Task Breakdown\n\n")
            f.write(f"**Generated:** {datetime.now().isoformat()}\n\n")
            f.write(str(tasks))
        
        # Also save as JSON if possible
        json_file = project_dir / "tasks" / "task_breakdown.json"
        try:
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(tasks if isinstance(tasks, (dict, list)) else {"tasks": str(tasks)}, f, indent=2)
        except:
            pass
        
        print(f"✅ Tasks saved to: {output_file}")
        return output_file
    
    def save_generated_code(self, project_dir: Path, code_files: Dict[str, str]):
        """Save generated code files"""
        code_dir = project_dir / "generated_code"
        
        for file_path, content in code_files.items():
            output_file = code_dir / file_path
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(content)
            
            print(f"✅ Code saved: {output_file}")
        
        return code_dir
    
    def save_infrastructure_configs(self, project_dir: Path, configs: Dict[str, str]):
        """Save infrastructure configuration files"""
        infra_dir = project_dir / "infrastructure"
        
        for file_path, content in configs.items():
            output_file = infra_dir / file_path
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(content)
            
            print(f"✅ Infrastructure config saved: {output_file}")
        
        return infra_dir
    
    def save_execution_summary(self, project_dir: Path, summary: Dict):
        """Save execution summary"""
        output_file = project_dir / "reports" / "execution_summary.json"
        
        summary_with_timestamp = {
            "execution_time": datetime.now().isoformat(),
            **summary
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(summary_with_timestamp, f, indent=2)
        
        # Also create markdown version
        md_file = project_dir / "reports" / "execution_summary.md"
        with open(md_file, 'w', encoding='utf-8') as f:
            f.write(f"# Execution Summary\n\n")
            f.write(f"**Execution Time:** {datetime.now().isoformat()}\n\n")
            
            for key, value in summary.items():
                f.write(f"## {key}\n\n")
                f.write(f"```\n{value}\n```\n\n")
        
        print(f"✅ Summary saved to: {output_file}")
        return output_file
    
    def create_project_readme(self, project_dir: Path, project_info: Dict):
        """Create a README for the project output"""
        readme_file = project_dir / "README.md"
        
        with open(readme_file, 'w', encoding='utf-8') as f:
            f.write(f"# {project_info.get('name', 'Generated Project')}\n\n")
            f.write(f"**Generated by:** CrewAI Coding Agents\n")
            f.write(f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            f.write(f"## Project Description\n\n")
            f.write(f"{project_info.get('description', 'No description provided')}\n\n")
            
            f.write(f"## Directory Structure\n\n")
            f.write(f"```\n")
            f.write(f"├── analysis/           # Analysis reports\n")
            f.write(f"├── architecture/       # Architecture designs\n")
            f.write(f"├── tasks/              # Task breakdowns\n")
            f.write(f"├── generated_code/     # Generated source code\n")
            f.write(f"├── infrastructure/     # Infrastructure configs\n")
            f.write(f"├── documentation/      # Additional documentation\n")
            f.write(f"└── reports/            # Execution reports\n")
            f.write(f"```\n\n")
            
            f.write(f"## Next Steps\n\n")
            f.write(f"1. Review the analysis reports in `analysis/`\n")
            f.write(f"2. Check the architecture design in `architecture/`\n")
            f.write(f"3. Review task breakdown in `tasks/`\n")
            f.write(f"4. Explore generated code in `generated_code/`\n")
            f.write(f"5. Review infrastructure configs in `infrastructure/`\n\n")
        
        print(f"✅ Project README created: {readme_file}")
        return readme_file
