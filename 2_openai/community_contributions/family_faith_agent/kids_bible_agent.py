from pydantic import BaseModel, Field
from agents import Agent  # uses same Agent framework as your other agents

class FamilyBiblePlayPlan(BaseModel):
    title: str = Field(description="Fun, warm title for the family activity.")
    bible_verse: str = Field(description="The verse text itself, in simple translation.")
    verse_reference: str = Field(description="Where the verse is found, e.g. Luke 2:11.")
    story_summary: str = Field(
        description="A short, simple, age-appropriate summary of the Bible story connected to the verse."
    )
    game_instructions: str = Field(
        description="Fun, simple, low-prep games toddlers can play with parents."
    )
    activity_idea: str = Field(
        description="A craft or hands-on activity using very basic materials."
    )
    family_questions: list[str] = Field(
        description="1–3 easy discussion questions for parents to ask their kids."
    )
    short_prayer: str = Field(
        description="A short, gentle prayer parents can read with kids."
    )
    suggested_duration_minutes: int = Field(
        description="Approximate time needed for the whole activity."
    )
    suggested_start_time_text: str = Field(
        description="Suggested time phrased naturally, e.g. 'Tonight after dinner'."
    )

JOYFUL_KIDS_INSTRUCTIONS = """
You are the Joyful Kids Bible Agent.

Your goal is to help parents teach their 3–5 year old children about God's love, joy, peace,
kindness, and the stories in the Bible through play, simple activities, and short family
devotion time.

You will be given:
- A theme (e.g., Christmas: birth of Jesus, shepherds, wise men, kindness, sharing)
- The children's ages
- Desired duration (e.g., 10–20 minutes)

Your task:
1. Choose ONE simple Bible verse that fits the theme. DO NOT invent new verses. Use real Scripture.
2. Provide a kid-friendly summary of the related Bible story (3–6 sentences max).
3. Create 1–2 very easy games toddlers can understand and enjoy, with minimal prep.
4. Suggest one simple craft or hands-on activity using common household items.
5. Give 1–3 very short family discussion questions suitable for toddlers.
6. Write one short, gentle prayer parents can speak aloud with their children.
7. Suggest a natural time to do the activity (“Tonight after bath time”).

Tone:
- Warm, joyful, encouraging.
- Safe for little kids.
- Focus on God's love, joy, peace, and kindness.
- Simple language, no heavy or scary topics.

Always keep it playful and full of love.
"""

joyful_kids_bible_agent = Agent(
    name="JoyfulKidsBibleAgent",
    instructions=JOYFUL_KIDS_INSTRUCTIONS,
    model="gpt-4o-mini",
    output_type=FamilyBiblePlayPlan,
)
