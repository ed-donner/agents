import os
import httpx
import gradio as gr
from dotenv import load_dotenv
from story_manager import StoryManager, UserInput

load_dotenv(override=True)


def send_pushover_notification(title: str, message: str):
    """Send a push notification via Pushover"""
    token = os.getenv("PUSHOVER_TOKEN")
    user = os.getenv("PUSHOVER_USER")
    if not token or not user:
        print("Pushover credentials not set")
        return
    try:
        httpx.post(
            "https://api.pushover.net/1/messages.json",
            data={
                "token": token,
                "user": user,
                "title": title,
                "message": message[:1024],
            },
        )
    except Exception as e:
        print(f"Pushover error: {e}")


async def generate_story(
    child_name: str,
    age: int,
    story_length: str,
    interests: list[str],
    special_character: str,
    moral_lesson: str,
    topics_to_avoid: str,
    include_fun_fact: bool,
    story_language: str,
):
    """Generate a bedtime story based on user input"""

    if not child_name:
        yield "Please enter the child's name!", ""
        return

    if not interests:
        yield "Please select at least one interest!", ""
        return

    user_input = UserInput(
        child_name=child_name,
        age=age,
        story_length=story_length,
        interests=interests,
        special_character=special_character if special_character else None,
        moral_lesson=moral_lesson,
        topics_to_avoid=topics_to_avoid if topics_to_avoid else None,
        include_fun_fact=include_fun_fact,
        story_language=story_language,
    )

    async for chunk in StoryManager().run(user_input):
        # Check if this is the final story (starts with #)
        if chunk.startswith("# ") or chunk.startswith("---"):
            # Send Pushover notification
            send_pushover_notification(
                f"Story created for {child_name}",
                f"Age: {age}, Length: {story_length}, Language: {story_language}",
            )
            yield "", chunk  # Clear status, show story
        else:
            yield chunk, ""  # Show status, clear story


# Build the Gradio UI
with gr.Blocks(
    theme=gr.themes.Soft(primary_hue="purple", secondary_hue="pink"),
    title="Bedtime Stories Creator",
) as ui:

    gr.Markdown("# 🌙 Bedtime Stories Creator")

    # Child's Name - separate box
    with gr.Group():
        child_name = gr.Textbox(label="Child's Name", placeholder="Enter name...")

    # Age - separate box with dropdown
    with gr.Group():
        age = gr.Dropdown(
            label="Age",
            choices=[2, 3, 4, 5, 6, 7, 8, 9, 10],
            value=5,
        )

    # Interests - separate box
    with gr.Group():
        interests = gr.Dropdown(
            label="Interests",
            choices=[
                # Animals & Nature
                "Animals",
                "Dinosaurs",
                "Ocean",
                "Nature",
                "Butterflies",
                "Birds",
                # Fantasy
                "Dragons",
                "Unicorns",
                "Fairies",
                "Magic",
                "Wizards",
                # Adventure
                "Pirates",
                "Space",
                "Superheroes",
                "Ninjas",
                "Knights",
                "Explorers",
                # Toys & Brands
                "LEGO",
                "Playmobil",
                "Hot Wheels",
                "Barbie",
                "Paw Patrol",
                "Peppa Pig",
                # Gaming
                "Minecraft",
                "Fortnite",
                "Roblox",
                "Pokemon",
                "Mario",
                "Gaming",
                "Brawlstar",
                # Vehicles
                "Trains",
                "Cars",
                "Airplanes",
                "Rockets",
                "Trucks",
                "Motorcycles",
                # Creative
                "Art",
                "Music",
                "Dancing",
                "Cooking",
                "Building",
                "Crafts",
                # Sports
                "Sports",
                "Soccer",
                "Basketball",
                "Swimming",
                "Martial Arts",
                # Characters
                "Princesses",
                "Robots",
                "Kings",
                "Queens",
            ],
            value=["Animals"],
            multiselect=True,
        )

    # Other options - all dropdowns
    with gr.Group():
        story_length = gr.Dropdown(
            label="Length", choices=["short", "medium", "long"], value="medium"
        )
        story_language = gr.Dropdown(
            label="Language", choices=["Hebrew", "English"], value="Hebrew"
        )
        moral_lesson = gr.Dropdown(
            label="Moral Lesson",
            choices=[
                "None",
                # Core values
                "Kindness",
                "Courage",
                "Honesty",
                "Patience",
                "Gratitude",
                # Social
                "Friendship",
                "Sharing",
                "Teamwork",
                "Helping Others",
                "Forgiveness",
                # Personal growth
                "Being Yourself",
                "Believing in Yourself",
                "Never Give Up",
                # Responsibility
                "Responsibility",
                "Hard Work",
                "Taking Care of Others",
                "Respecting Nature",
                # Emotional
                "Overcoming Fear",
                "Dealing with Change",
            ],
            value="Kindness",
        )

    # Optional fields
    with gr.Accordion("More Options", open=False):
        special_character = gr.Textbox(
            label="Special Character", placeholder="Fluffy the cat"
        )
        topics_to_avoid = gr.Textbox(label="Topics to Avoid", placeholder="water, dogs")
        include_fun_fact = gr.Checkbox(label="Include Fun Fact", value=True)

    # Button
    generate_btn = gr.Button("✨ Create Story", variant="primary", size="lg")

    # Status
    status_output = gr.Markdown(value="")

    # Story output
    story_output = gr.Markdown(value="", rtl=True)

    gr.Markdown("🛡️ *Stories reviewed for child safety. AI can make mistakes.*")

    # Wire up the button
    generate_btn.click(
        fn=generate_story,
        inputs=[
            child_name,
            age,
            story_length,
            interests,
            special_character,
            moral_lesson,
            topics_to_avoid,
            include_fun_fact,
            story_language,
        ],
        outputs=[status_output, story_output],
    )

if __name__ == "__main__":
    ui.launch(inbrowser=True)
