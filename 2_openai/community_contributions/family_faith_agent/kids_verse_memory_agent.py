from pydantic import BaseModel, Field
from agents import Agent

class VerseMemoryPlan(BaseModel):
    call_and_response: str = Field(
        description="A simple call-and-response way to say the verse with kids."
    )
    motions_description: str = Field(
        description="A line-by-line description of simple hand/body motions to go with the verse."
    )
    repetition_game: str = Field(
        description="A short game that repeats the verse (whisper voice, loud voice, clap, etc.)."
    )
    encouragement_words: str = Field(
        description="Short encouragement for parents to cheer their kids on."
    )

VERSE_MEMORY_INSTRUCTIONS = """
You are the Little Seeds Verse Memory Agent.

You help parents and 3–5 year old kids memorize a short Bible verse using:
- Simple call-and-response
- Fun hand motions
- A very short repetition game

You will be given:
- The verse text
- The reference (e.g., Luke 2:11)
- The theme (e.g., Christmas, joy, peace)

Your output:
1. A simple call-and-response pattern for parent and child to repeat the verse.
2. A line-by-line description of simple, safe hand/body motions to pair with words or phrases.
3. One very short repetition game (e.g., whisper, clap, stomp, freeze, etc.).
4. Warm, brief encouragement for parents to celebrate effort, not perfection.

Keep it short, joyful, and age-appropriate.
"""

joyful_kids_verse_memory_agent = Agent(
    name="LittleSeedsVerseMemoryAgent",
    instructions=VERSE_MEMORY_INSTRUCTIONS,
    model="gpt-4o-mini",
    output_type=VerseMemoryPlan,
)
