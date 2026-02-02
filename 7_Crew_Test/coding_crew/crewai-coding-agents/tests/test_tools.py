"""
Tests for tools
"""
import pytest
from tools.code_tools import CodeGenerationTool, CodeAnalysisTool
from tools.infrastructure_tools import DockerTool, KubernetesTool
from tools.cicd_tools import GitHubActionsTool


class TestCodeGenerationTool:
    """Tests for CodeGenerationTool"""
    
    def test_initialization(self):
        """Test tool initialization"""
        tool = CodeGenerationTool()
        assert tool.name == "Code Generation Tool"
    
    def test_run_python_model(self):
        """Test generating Python model"""
        tool = CodeGenerationTool()
        result = tool._run(
            language="python",
            framework="fastapi",
            component_type="model",
            component_name="User",
            specifications="User model with email and name"
        )
        assert "class" in result or "Generated" in result


class TestDockerTool:
    """Tests for DockerTool"""
    
    def test_python_dockerfile(self):
        """Test generating Python Dockerfile"""
        tool = DockerTool()
        result = tool._run(
            language="python",
            framework="fastapi",
            app_name="myapp",
            port=8080
        )
        assert "FROM python" in result
        assert "EXPOSE 8080" in result
    
    def test_go_dockerfile(self):
        """Test generating Go Dockerfile"""
        tool = DockerTool()
        result = tool._run(
            language="go",
            framework="gin",
            app_name="myapp",
            port=8080
        )
        assert "FROM golang" in result


class TestKubernetesTool:
    """Tests for KubernetesTool"""
    
    def test_deployment_generation(self):
        """Test generating Kubernetes deployment"""
        tool = KubernetesTool()
        result = tool._run(
            resource_type="deployment",
            name="myapp",
            namespace="default",
            spec={"replicas": 3, "image": "myapp:latest", "port": 8080}
        )
        assert "kind: Deployment" in result
        assert "replicas: 3" in result


class TestGitHubActionsTool:
    """Tests for GitHubActionsTool"""
    
    def test_workflow_generation(self):
        """Test generating GitHub Actions workflow"""
        tool = GitHubActionsTool()
        result = tool._run(
            workflow_name="CI/CD Pipeline",
            language="python",
            triggers=["push", "pull_request"],
            include_deploy=True,
            deploy_target="kubernetes"
        )
        assert "name: CI/CD Pipeline" in result
        assert "push:" in result
