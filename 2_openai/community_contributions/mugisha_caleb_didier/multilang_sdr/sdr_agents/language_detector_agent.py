from agents import Agent
from models.schemas import LanguageDetection

INSTRUCTIONS = """You are a language detection agent. Analyze the given text and identify its dominant language.

Return the language name (e.g. "English", "French", "Kinyarwanda") and your confidence score from 0.0 to 1.0."""

language_detector_agent = Agent(
    name="Language Detector",
    instructions=INSTRUCTIONS,
    model="gpt-4o-mini",
    output_type=LanguageDetection,
)
