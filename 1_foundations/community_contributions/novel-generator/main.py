from agents import Agent, WebSearchTool, trace, Runner, gen_trace_id, function_tool
from agents.model_settings import ModelSettings
from pydantic import BaseModel, Field
from dotenv import load_dotenv
import asyncio
import os
import itertools  # Needed for loading animation
from typing import Dict
from IPython.display import display, Markdown

load_dotenv(override=True)

# Async loading indicator that runs until the event is set
async def show_loading_indicator(done_event):
    for dots in itertools.cycle(['', '.', '..', '...']):
        if done_event.is_set():
            break
        print(f'\rGenerating{dots}', end='', flush=True)
        await asyncio.sleep(0.5)
    print('\rDone generating!     ')  # Clear the line when done

def prompt_with_default(prompt_text, default_value=None, cast_type=str):
    user_input = input(f"{prompt_text} ")
    if user_input.strip() == "":
        return default_value
    try:
        return cast_type(user_input)
    except ValueError:
        print(f"Invalid input. Using default: {default_value}")
        return default_value

def get_user_inputs():
    # 1. Novel genre
    genre = prompt_with_default("Novel genre (press Enter for default - teen mystery):", "teen mystery")

    # 2. General plot
    plot = input("\nGeneral plot (Enter for auto-generated plot): ").strip()
    if not plot:
        plot = "Auto-Generated Plot"

    # 3. Title
    title = input("\nTitle (Enter for auto-generated title): ").strip()
    if not title:
        title = "Auto-Generated Title"

    # 4. Number of pages
    num_pages = prompt_with_default("\nNumber of pages in novel (Enter for default - 90 pages):", 90, int)
    num_words = num_pages * 275

    # 5. Number of chapters
    num_chapters = prompt_with_default("\nNumber of chapters (Enter for default - 15):", 15, int)

    # 6. Max AI tokens
    while True:
        max_tokens_input = input(
            "\nMaximum AI tokens to use, after which novel \n"
            "generation will fail (about 200,000 tokens for 90): "
        ).strip()
        try:
            max_tokens = int(max_tokens_input)
            if max_tokens <= 0:
                print("Please enter a positive integer.")
                continue

            if max_tokens > 300000:
                print(f"\n⚠️  You entered {max_tokens:,} tokens, which is quite high and may be expensive.")
                confirm = input("Are you sure you want to use this value? (Yes or No): ").strip().lower()
                if confirm != "yes":
                    print("Okay, let's try again.\n")
                    continue  # Ask again

            break  # Valid and confirmed
        except ValueError:
            print("Please enter a valid integer.")
    return genre, title, num_pages, num_words, num_chapters, plot, max_tokens

async def generate_novel(genre, title, num_pages, num_words, num_chapters, plot, max_tokens):
    # Print collected inputs for confirmation (optional)
    print("\nCOLLECTED NOVEL CONFIGURATION:\n")
    print(f"Genre: {genre}")
    print(f"Plot: {plot}")
    print(f"Title: {title}")
    print(f"Pages: {num_pages}")
    print(f"Chapters: {num_chapters}")
    print(f"Max Tokens: {max_tokens}")

    print("\nAwesome, now we'll generate your novel!")

    INSTRUCTIONS = f"You are a fiction author assistant. You will use user-provided parameters, \
    or default parameters, to generate a creative and engaging novel. \
    Do not perform web searches. Focus entirely on imaginative, coherent, and emotionally engaging content. \
    Your output should read like a real novel, vivid, descriptive, and character-driven. \
    \
    If the user input plot is \"Auto-Generated Plot\" then you should generate an interesting plot for the novel \
    based on the genre, otherwise use the plot provided by the user. \
    \
    If the user input title is \"Auto-Generated Title\" then you should generate an interesting title \
    based on the genre and plot, otherwise use the title provided by the user. \
    \
    The genre of the novel is {genre}. The plot of the novel is {plot}. The title of the novel is {title}. \
    You should generate a novel that is {num_pages} pages long. Ensure you do not abruptly end the novel \
    just to match the specified number of pages. So ensure the story naturally concludes leading up to the end. \
    The novel should be broken up into {num_chapters} chapters. Each chapter should develop the characters and \
    the story in an interesting and engaging way. \
    \
    Do not include any markdown or formatting symbols (e.g., ###, ---, **, etc.). \
    Use plain text only: start with the title, followed by chapter titles and their respective story content. \
    Do not include a conclusion or author notes at the end. End the story when the final chapter ends naturally. \
    \
    The story should contain approximately {num_words} words to match a target of {num_pages} standard paperback pages. \
    Each chapter should contribute proportionally to the total word count. \
    Continue generating story content until the target word count is reached or slightly exceeded. \
    Do not summarize or compress events to shorten the story."

    search_agent = Agent(
        name="Novel Generator Agent",
        instructions=INSTRUCTIONS,
        model="gpt-4o-mini",
        model_settings=ModelSettings(
            temperature=0.8,
            top_p=0.9,
            frequency_penalty=0.5,
            presence_penalty=0.6,
            max_tokens=max_tokens
        )
    )

    message = f"Generate a {genre} novel titled '{title}' with {num_pages} pages."

    with trace("Search"):
        result = await Runner.run(
            search_agent, 
            message
        )

    return result.final_output

# Your agent call with loading indicator
async def main():
    done_event = asyncio.Event()
    loader_task = asyncio.create_task(show_loading_indicator(done_event))

    # Run the agent
    genre, title, num_pages, num_words, num_chapters, plot, max_tokens = get_user_inputs()

    result = await generate_novel(
        genre, title, num_pages, num_words, num_chapters, plot, max_tokens
    )

    # Signal that loading is done
    done_event.set()
    await loader_task  # Let it finish cleanly

    # Output result to file
    lines = result.strip().splitlines()
    generated_title = "untitled_novel"
    for line in lines:
        if line.strip():  # skip empty lines
            generated_title = line.strip()
            break

    # Sanitize title for filename
    filename_safe_title = ''.join(c if c.isalnum() or c in (' ', '_', '-') else '_' for c in generated_title).strip().replace(' ', '_')
    output_path = os.path.abspath(f"novel_{filename_safe_title}.txt")

    # Save to file
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(result)

    # Show full path
    print(f"\n📘 Novel saved to: {output_path}")

if __name__ == "__main__":
    asyncio.run(main())