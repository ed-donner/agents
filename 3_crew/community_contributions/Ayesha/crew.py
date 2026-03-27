import os
import json
import litellm
from crewai import LLM
from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from pydantic import BaseModel, Field
from typing import List

USE_OLLAMA = True

if USE_OLLAMA:
    llm = LLM(
        model="ollama/llama3.2",
        base_url="http://localhost:11434",
        temperature=0.1,
        format="json"
    )
else:
    llm = LLM(
        model="openai/gpt-4o-mini"  
    )

class EmotionAnalysis(BaseModel):
    emotion: str = Field(description="Detected primary emotion")
    intensity: str = Field(description="Low, medium, or high intensity")
    causes: List[str] = Field(description="Possible causes of the emotion")


class MindBodyInsight(BaseModel):
    physiological_needs: List[str] = Field(description="Physiological needs based on emotion")
    explanation: str = Field(description="Why these needs are important")

class FoodItems(BaseModel):
    name: str = Field(description="Food name")
    justification: str = Field(description="Why it helps")

class FoodRecommendation(BaseModel):
    foods: List[FoodItems] = Field(description="Recommended foods")
    reasoning: str = Field(description="Why these foods help")

class Habit(BaseModel):
    habit: str = Field(description="Habit name")
    instructions: str = Field(description="How to perform the habit")
    rationale: str = Field(description="Why it helps emotionally or physiologically")


class HabitRecommendation(BaseModel):
   habits: List[Habit] = Field(description="Suggested habits")


class FinalResponse(BaseModel):
    response: str = Field(description="Final empathetic response to the user")


@CrewBase
class AffectAI():
    """AffectAI crew: Emotion-aware food & habit recommendation system"""

    agents_config = 'config/agents.yaml'
    tasks_config = 'config/tasks.yaml'


    @agent
    def emotion_analyst(self) -> Agent:
        return Agent(
            config=self.agents_config['emotion_analyst'],
            llm = llm,
            memory=False
        )

    @agent
    def mindfulness_analyst(self) -> Agent:
        return Agent(
            config=self.agents_config['mindfulness_analyst'],
             llm = llm,
        )

    @agent
    def nutrition_advisor(self) -> Agent:
        return Agent(
            config=self.agents_config['nutrition_advisor'],
            llm = llm,
        )

    @agent
    def habits_coach(self) -> Agent:
        return Agent(
            config=self.agents_config['habits_coach'],
            llm = llm,
        )

    @agent
    def communication_coach(self) -> Agent:
        return Agent(
            config=self.agents_config['communication_coach'],
            memory=False,
            llm = llm,
        )

    # @agent
    # def manager(self) -> Agent:
    #     return Agent(
    #         config=self.agents_config['manager'],
    #         allow_delegation=True
    #     )


    @task
    def analyze_emotion(self) -> Task:
        return Task(
            config=self.tasks_config['analyze_emotion'],
            output_json=EmotionAnalysis
        )

    @task
    def map_mind_body(self) -> Task:
        return Task(
            config=self.tasks_config['map_mind_body'],
            # output_json=MindBodyInsight
        )

    @task
    def recommend_food(self) -> Task:
        return Task(
            config=self.tasks_config['recommend_food'],
            # output_json=FoodRecommendation
        )

    @task
    def suggest_habits(self) -> Task:
        return Task(
            config=self.tasks_config['suggest_habits'],
            # output_json=HabitRecommendation
        )

    @task
    def generate_response(self) -> Task:
        return Task(
            config=self.tasks_config['generate_response'],
            # output_json=FinalResponse
        )

    @crew
    def crew(self) -> Crew:
        """Creates the AffectAI crew"""

        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
            memory=False,
        )