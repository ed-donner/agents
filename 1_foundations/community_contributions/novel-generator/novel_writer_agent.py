from agents import Agent, gen_trace_id, ModelSettings, Runner, trace

async def generate_novel(genre, title, num_pages, num_words, num_chapters, plot, max_tokens):
  INSTRUCTIONS = f"You are a fiction author assistant. You will use user-provided parameters, \
  or default parameters, to generate a creative and engaging novel. \
  Do not perform web searches. Focus entirely on imaginative, coherent, and emotionally engaging content. \
  Your output should read like a real novel, vivid, descriptive, and character-driven. \
  \
  If the user input plot is \"Auto-Generated Plot\" then you should generate an interesting plot for the novel \
  based on the genre, otherwise use the plot provided by the user. \
  \
  If the user provides the title 'Auto-Generated Title', then you must generate a creative, natural-sounding \
  title for the book, based on the genre and plot. \
  ⚠️ Do not include words like 'title', 'novel', or 'auto-generated' in the title. \
  ✅ The result must be a clean, human-like book title such as 'The Whispering Shadows' or 'Echoes of Tomorrow', \
  not a filename, not prefixed with 'novel_', and not using underscores. If the user provided their own title \
  (i.e., not 'Auto-Generated Title'), use it exactly as given.  \
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

  novel_writer_agent = Agent(
      name="Novel Writer Agent",
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

  generate_novel_trace_id = gen_trace_id()
  result = await Runner.run(
      novel_writer_agent, 
      message
  )

  return result.final_output