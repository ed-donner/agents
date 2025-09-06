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
    plot = input("General plot (Enter for auto-generated plot): ").strip()
    if not plot:
        plot = "Auto-Generated Plot"

    # 3. Title
    title = input("Title (Enter for auto-generated title): ").strip()
    if not title:
        title = "Auto-Generated Title"

    # 4. Number of pages
    num_pages = prompt_with_default("Number of pages in novel (Enter for default - 90 pages):", 90, int)
    num_words = num_pages * 275

    # 5. Number of chapters
    num_chapters = prompt_with_default("Number of chapters (Enter for default - 15):", 15, int)

    # 6. Max AI tokens
    while True:
        max_tokens_input = input(
            "\nMaximum AI tokens to use. Note that if the max tokens is not high enough, \
            the novel might not be completely generated. (about 50,000 - 200,000 tokens for 90): "
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
    print(f"\nGenre: {genre}")
    print(f"Plot: {plot}")
    print(f"Title: {title}")
    print(f"Pages: {num_pages}")
    print(f"Chapters: {num_chapters}")
    print(f"Max Tokens: {max_tokens}")
    return genre, title, num_pages, num_words, num_chapters, plot, max_tokens