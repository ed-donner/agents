from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai.agents.agent_builder.base_agent import BaseAgent
from pydantic import BaseModel, Field
from typing import List
from crewai_tools import SerperDevTool


class NewsInformation(BaseModel):
    'A class representing the information needed to write a news article.'
    title: str = Field(description="The title of the news article.")
    content: str = Field(description="The content of the news article.")
    source: str = Field(description="The source of the news article.")
    
class NewsInformationsList(BaseModel):
    'A class representing a list of news information.'
    news_informations: List[NewsInformation] = Field(description="A list of news information.")
    
# class WrittenNewsArticle(BaseModel):
#     'A class representing a written news article.'
#     title: str = Field(description="The title of the written news article.")
#     content: str = Field(description="The content of the written news article.")
#     source: str = Field(description="The source of the written news article.")
    
# class WrittenNewsArticlesList(BaseModel):
#     'A class representing a list of written news articles.'
#     written_news_articles: List[WrittenNewsArticle] = Field(description="A list of written news articles.")


@CrewBase
class NewsCrew():

    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"

    @agent
    def news_finder(self) -> Agent:
        return Agent(
            config=self.agents_config['news_finder'],
            tools=[SerperDevTool()]
        )

    @agent
    def news_writer(self) -> Agent:
        return Agent(
            config=self.agents_config['news_writer']
        )

    @task
    def find_news_task(self) -> Task:
        return Task(
            config=self.tasks_config['find_news_task'],
            max_retries=3,
            output_pydantic=NewsInformationsList
        )

    @task
    def write_news_report_task(self) -> Task:
        return Task(
            config=self.tasks_config['write_news_report_task'],
            max_retries=3, 
        )

    @crew
    def crew(self) -> Crew:

        manager = Agent(
            config=self.agents_config['manager'],
            allow_delegation=True
        )

        return Crew(
            manager=manager,
            agents=self.agents,
            tasks=self.tasks,
            verbose=True
        )
# @CrewBase
# class NewsCrew():
#     'A crew agent that writes news articles based on given information.'
    
#     agents_config: Agent = 'config/agents.yaml'
#     task_config: Task = 'config/tasks.yaml'
    
#     @agent
#     def news_finder_agent(self) -> Agent:
#         print("AGENTS CONFIG:", self.agents_config)
#         'An agent that gathers news information from various sources.'
#         return Agent(
#             config=self.agents_config['news_finder'],
#             tools=[SerperDevTool()]
#         ) 
    
#     @agent
#     def news_writer_agent(self) -> Agent:
#         'An agent that writes news articles based on the gathered information.'
#         return Agent(
#             config=self.agents_config['news_writer']
#         )
        
#     @task
#     def find_news_article(self, news_informations: NewsInformationsList) -> WrittenNewsArticlesList:
#         'A task that takes in a list of news information and returns a list of written news articles.'
#         return Task(
#             config=self.task_config['find_news_task'],
#             output_pydantic=NewsInformationsList
#         ) 
        
#     @task
#     def write_news_article(self, news_informations: NewsInformationsList) -> WrittenNewsArticlesList:
#         'A task that takes in a list of news information and returns a list of written news articles.'
#         return Task(
#             config=self.task_config['write_news_task'],
#             output_pydantic=WrittenNewsArticlesList
#         )
        
#     @crew
#     def news_writing_crew(self) -> Crew:
#         'A crew that coordinates the news finding, summarizing, and writing tasks.'
        
#         manager = Agent(
#             config=self.agents_config['manager'],
#             allow_delegation=True
#         )
        
#         return Crew(
#             manager=manager,
#             agents=self.agents,
#             tasks=self.tasks,
#             verbose=True,
#             manager_agent=manager
#         )