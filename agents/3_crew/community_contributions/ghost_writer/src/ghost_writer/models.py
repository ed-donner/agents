from pydantic import BaseModel, Field
from typing import List

class Idea(BaseModel):
    """Idea for the novel"""
    premise: str = Field(..., description="The premise of the novel")
    theme: str = Field(..., description="The theme of the novel")
    characters: str = Field(..., description="The main characters of the novel")
    plot_concepts: str = Field(..., description="The plot concepts of the novel")

class Plot(BaseModel):
    """Plot for the novel"""
    description: str = Field(..., description="A brief description of the plot")
    rising_action: str = Field(..., description="The rising action of the plot")
    climax: str = Field(..., description="The climax of the plot")
    falling_action: str = Field(..., description="The falling action of the plot")
    resolution: str = Field(..., description="The resolution of the plot")

class Character(BaseModel):
    """Character for the novel"""
    name: str = Field(..., description="The name of the character")
    role: str = Field(..., description="The role of the character, e.g., 'Protagonist'")
    traits: str = Field(..., description="The traits of the character, e.g., 'Brave and Determined'")
    backstory: str = Field(..., description="The backstory of the character")
    motivations: str = Field(..., description="The motivations of the character")
    flaws: str = Field(..., description="The flaws of the character")
    relationships: str = Field(..., description="The relationships of the character")

class Characters(BaseModel):
    """Characters for the novel"""
    characters: List[Character] = Field(..., description="List of characters in the novel")

class Scene(BaseModel):
    """Scene for the novel"""
    scene_description: str = Field(..., description="A brief description of the scene")
    scene_title: str = Field(..., description="The title of the scene, e.g., 'The Dark Forest'")
    characters: str = Field(..., description="The characters involved in the scene")
    scene_plot: str = Field(..., description="The plot of the scene")
    
class Chapter(BaseModel):
    """Outline node for the novel"""
    chapter_title: str = Field(..., description="The title of the chapter, e.g., 'The Beginning'")
    chapter_description: str = Field(..., description="A brief description of the chapter")
    chapter_plot: str = Field(..., description="The plot of the chapter")
    scenes: List[Scene] = Field(..., description="List of scenes in the chapter")

class Act(BaseModel):
    """Act for the novel"""
    act_number: int = Field(..., description="The act number, e.g., 2")
    act_title: str = Field(..., description="The title of the act, e.g., 'The Journey Begins'")
    act_description: str = Field(..., description="A brief description of the act")
    act_plot: str = Field(..., description="The plot of the act")
    chapters: List[Chapter] = Field(..., description="List of chapters in the act")

class Book(BaseModel):
    title: str = Field(..., description="The title of the book")
    author: str = Field(..., description="The author of the book")
    description: str = Field(..., description="A brief description of the book")

class ArtisticVision(BaseModel):
    """Artistic vision for the novel"""
    genre: str = Field(..., description="The genre of the book, e.g., 'Fantasy'")
    tone: str = Field(..., description="The tone of the book, e.g., 'Dark and Mysterious'")
    style: str = Field(..., description="The style of the book, e.g., 'Gothic'")
    themes: str = Field(..., description="The themes of the book, e.g., 'Love and Betrayal'")
    target_audience: str = Field(..., description="The target audience for the book, e.g., 'Young Adults'")
    visual_elements: str = Field(..., description="The visual elements of the book, e.g., 'Dark Colors and Shadows'")
    color_palette: str = Field(..., description="The color palette for the book, e.g., 'Black, Red, and White'")
    description: str = Field(..., description="A brief description of the artistic vision")