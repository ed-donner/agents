import abc

from agents import Agent, Tool


class AgentModel(abc.ABC):
    agent: Agent

    @abc.abstractmethod
    def init_agent(self):
        """Initialize and return the agent."""
        pass

    @property
    def agent_instance(self) -> Agent:
        """Return the agent instance."""
        return self.agent

    @abc.abstractmethod
    def as_tool(self) -> Tool:
        """Return the agent as a tool."""
        pass
