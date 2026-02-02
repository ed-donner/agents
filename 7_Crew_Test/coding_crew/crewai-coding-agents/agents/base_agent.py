"""
Base agent class with common functionality
"""
from abc import ABC, abstractmethod
from typing import List, Optional, Any
from crewai import Agent
from config.llm_config import get_llm_for_role


class BaseAgent(ABC):
    """Abstract base class for all agents"""
    
    def __init__(self):
        self._agent: Optional[Agent] = None
        self._tools: List[Any] = []
        self._setup_tools()
    
    @property
    @abstractmethod
    def role(self) -> str:
        """Agent's role"""
        pass
    
    @property
    @abstractmethod
    def goal(self) -> str:
        """Agent's goal"""
        pass
    
    @property
    @abstractmethod
    def backstory(self) -> str:
        """Agent's backstory"""
        pass
    
    @property
    def llm_type(self) -> str:
        """LLM type for this agent"""
        return "coder"
    
    @property
    def tools(self) -> List[Any]:
        """Agent's tools"""
        return self._tools
    
    @abstractmethod
    def _setup_tools(self) -> None:
        """Setup agent-specific tools"""
        pass
    
    def get_agent(self) -> Agent:
        """Get or create the CrewAI agent"""
        if self._agent is None:
            self._agent = Agent(
                role=self.role,
                goal=self.goal,
                backstory=self.backstory,
                tools=self.tools,
                llm=get_llm_for_role(self.llm_type),
                verbose=True,
                allow_delegation=self._allow_delegation(),
                max_iter=15,
                memory=True
            )
        return self._agent
    
    def _allow_delegation(self) -> bool:
        """Whether this agent can delegate tasks"""
        return False
    
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(role='{self.role}')"
