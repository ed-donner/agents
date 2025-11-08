from multiprocessing import process
from crewai import Agent, Crew, Process, Task, LLM
from crewai.project import CrewBase, agent, crew, task
from crewai.agents.agent_builder.base_agent import BaseAgent
from crewai_tools import FirecrawlSearchTool
from summarize.tools import PushoverNotificationTool
from typing import List
import os

ollama_llm = LLM(
    model="ollama/qwen3:1.7b",
    base_url="http://localhost:11434"
)

# Gemini LLM for article summarizer
gemini_llm = LLM(
    model="gemini-2.0-flash",
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
    api_key="AIzaSyBJ9o-JmyACGZeeZA_mRZ5vHmO3q6gn2t0"
)

firecrawl_tool = FirecrawlSearchTool(api_key="fc-828135b79cff4d9b8a53c1259c0cbaa6")
pushover_tool = PushoverNotificationTool()


@CrewBase
class Summarize():
    """Summarize crew"""

    agents: List[BaseAgent]
    tasks: List[Task]

    # Agents
    @agent
    def researcher(self) -> Agent:
        return Agent(
            config=self.agents_config['researcher'], 
            verbose=True,
            llm=gemini_llm,
            # tools=[firecrawl_tool]  # FirecrawlSearchTool enables web search capabilities
        )

    @agent
    def article_picker(self) -> Agent:  
        return Agent(
            config=self.agents_config['article_picker'], 
            verbose=True,
            llm=ollama_llm
        )

    @agent
    def article_summarizer(self) -> Agent:
        return Agent(
            config=self.agents_config['article_summarizer'], 
            verbose=True,
            llm=gemini_llm,
            tools=[pushover_tool]  # PushoverNotificationTool enables sending notifications
        )

    # Tasks
    @task
    def research_task(self) -> Task:
        return Task(
            config=self.tasks_config['research_task'],
            output_file='research.md'
        )

    @task
    def article_picker_task(self) -> Task:
        return Task(
            config=self.tasks_config['article_picker_task'],
            context=[self.research_task()],
            output_file='selected_article.md'
        )

    @task
    def article_summarizer_task(self) -> Task:
        return Task(
            config=self.tasks_config['article_summarizer_task'],
            context=[self.article_picker_task()],
            output_file='article_summary.md'
        )


    @crew
    def crew(self) -> Crew:
        """Creates the Summarize crew"""
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
        )
