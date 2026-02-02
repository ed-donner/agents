"""
Team Manager Agent - Orchestrates all other agents
"""
from typing import List, Dict, Any
from crewai import Agent
from .base_agent import BaseAgent
from config.llm_config import get_llm_for_role


class TeamManagerAgent(BaseAgent):
    """Team Manager that orchestrates the development team"""
    
    @property
    def role(self) -> str:
        return "Technical Team Manager"
    
    @property
    def goal(self) -> str:
        return """
        Lead the development team to successfully deliver high-quality software projects.
        Analyze requirements, design architecture, decompose work into tasks,
        assign tasks to appropriate team members, and ensure successful delivery.
        """
    
    @property
    def backstory(self) -> str:
        return """
        You are a seasoned Technical Team Manager with 15+ years of experience in software development.
        You have led multiple successful projects across various domains including e-commerce,
        fintech, healthcare, and enterprise systems.
        
        Your expertise includes:
        - Analyzing complex requirements and translating them into technical specifications
        - Designing scalable and maintainable software architectures
        - Breaking down large projects into manageable tasks
        - Matching tasks to team members based on their expertise
        - Managing project timelines and identifying risks
        - Ensuring code quality and best practices
        
        You have deep knowledge of:
        - Multiple programming languages (Python, Go, Node.js, C#, Ruby)
        - Frontend frameworks (React, Angular, Next.js)
        - Cloud platforms (AWS, Azure, GCP)
        - DevOps practices and CI/CD pipelines
        - Database design and optimization
        - Security best practices
        
        You are known for your ability to see the big picture while also understanding
        technical details, making you an effective bridge between business requirements
        and technical implementation.
        """
    
    @property
    def llm_type(self) -> str:
        return "manager"
    
    def _setup_tools(self) -> None:
        """Team Manager doesn't need specific tools - uses LLM capabilities"""
        self._tools = []
    
    def _allow_delegation(self) -> bool:
        """Team Manager can delegate tasks"""
        return True
    
    def get_agent(self) -> Agent:
        """Get Team Manager agent with manager role enabled"""
        if self._agent is None:
            self._agent = Agent(
                role=self.role,
                goal=self.goal,
                backstory=self.backstory,
                tools=self.tools,
                llm=get_llm_for_role(self.llm_type),
                verbose=True,
                allow_delegation=True,
                max_iter=25,
                memory=True
            )
        return self._agent
