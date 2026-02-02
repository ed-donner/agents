"""
Tests for agent classes
"""
import pytest
from unittest.mock import patch, MagicMock

from agents import (
    TeamManagerAgent,
    AnalystAgent,
    BackendEngineerFactory,
    FrontendEngineerFactory,
    DevOpsEngineer,
    DatabaseEngineer,
    QAEngineer
)


class TestTeamManagerAgent:
    """Tests for TeamManagerAgent"""
    
    def test_initialization(self):
        """Test agent initialization"""
        agent = TeamManagerAgent()
        assert agent.role == "Technical Team Manager"
        assert agent._allow_delegation() == True
    
    def test_goal_and_backstory(self):
        """Test goal and backstory are set"""
        agent = TeamManagerAgent()
        assert len(agent.goal) > 0
        assert len(agent.backstory) > 0


class TestBackendEngineerFactory:
    """Tests for BackendEngineerFactory"""
    
    def test_create_python_engineer(self):
        """Test creating Python backend engineer"""
        engineer = BackendEngineerFactory.create("python")
        assert engineer.language == "Python"
        assert "FastAPI" in engineer.frameworks
    
    def test_create_go_engineer(self):
        """Test creating Go backend engineer"""
        engineer = BackendEngineerFactory.create("go")
        assert engineer.language == "Go"
        assert "Gin" in engineer.frameworks
    
    def test_create_nodejs_engineer(self):
        """Test creating Node.js backend engineer"""
        engineer = BackendEngineerFactory.create("nodejs")
        assert engineer.language == "Node.js"
        assert "NestJS" in engineer.frameworks
    
    def test_unsupported_language(self):
        """Test error for unsupported language"""
        with pytest.raises(ValueError):
            BackendEngineerFactory.create("unsupported")


class TestFrontendEngineerFactory:
    """Tests for FrontendEngineerFactory"""
    
    def test_create_react_engineer(self):
        """Test creating React engineer"""
        engineer = FrontendEngineerFactory.create("react")
        assert engineer.framework == "React"
    
    def test_create_angular_engineer(self):
        """Test creating Angular engineer"""
        engineer = FrontendEngineerFactory.create("angular")
        assert engineer.framework == "Angular"
    
    def test_create_nextjs_engineer(self):
        """Test creating Next.js engineer"""
        engineer = FrontendEngineerFactory.create("nextjs")
        assert engineer.framework == "Next.js"


class TestAnalystAgent:
    """Tests for AnalystAgent"""
    
    def test_initialization(self):
        """Test analyst initialization"""
        analyst = AnalystAgent()
        assert analyst.role == "Project Analyst"
        assert len(analyst.tracked_tasks) == 0
    
    def test_progress_report_empty(self):
        """Test progress report with no tasks"""
        analyst = AnalystAgent()
        report = analyst.get_progress_report()
        assert report["total_tasks"] == 0
        assert report["completion_percentage"] == 0.0
