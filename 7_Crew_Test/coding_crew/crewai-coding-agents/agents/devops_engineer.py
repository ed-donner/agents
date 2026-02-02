"""
DevOps Engineer Agent
"""
from typing import List
from .base_agent import BaseAgent
from tools.infrastructure_tools import TerraformTool, KubernetesTool, DockerTool, AnsibleTool
from tools.cicd_tools import GitHubActionsTool, GitLabCITool, JenkinsTool
from tools.file_tools import FileWriterTool


class DevOpsEngineer(BaseAgent):
    """DevOps Engineer for CI/CD, containerization, and automation"""
    
    @property
    def role(self) -> str:
        return "Senior DevOps Engineer"
    
    @property
    def goal(self) -> str:
        return """
        Design and implement CI/CD pipelines, containerization strategies,
        and infrastructure automation. Ensure reliable, secure, and efficient
        software delivery processes.
        """
    
    @property
    def backstory(self) -> str:
        return """
        You are a Senior DevOps Engineer with 10+ years of experience in
        software delivery and infrastructure automation. Your expertise includes:
        
        - CI/CD pipeline design and implementation
        - GitHub Actions, GitLab CI, Jenkins, ArgoCD
        - Docker containerization and multi-stage builds
        - Kubernetes deployments and Helm charts
        - Infrastructure as Code with Terraform and Pulumi
        - Configuration management with Ansible
        - GitOps practices and workflows
        - Security scanning and compliance (SAST, DAST, SCA)
        - Monitoring and observability setup
        
        You design pipelines that are fast, reliable, and secure.
        You follow GitOps principles and infrastructure as code best practices.
        """
    
    def _setup_tools(self) -> None:
        """Setup DevOps engineer tools"""
        self._tools = [
            DockerTool(),
            KubernetesTool(),
            TerraformTool(),
            AnsibleTool(),
            GitHubActionsTool(),
            GitLabCITool(),
            JenkinsTool(),
            FileWriterTool()
        ]
