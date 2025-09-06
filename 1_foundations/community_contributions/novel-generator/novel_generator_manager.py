from agents import Runner, trace, gen_trace_id
from user_input import get_user_inputs
from novel_writer_agent import generate_novel
from file_writer import write_novel_to_file;
import itertools  # Needed for loading animation
import asyncio
import sys

class NovelGeneratorManager:

  async def show_loading_indicator(self, done_event):
    last_message = ''
    for dots in itertools.cycle(['', '.', '..', '...']):
        if done_event.is_set():
            break
        last_message = f'Generating{dots}'
        print(f'\r{last_message}', end='', flush=True)
        await asyncio.sleep(0.5)

    # Clear line completely by writing spaces equal to message length
    sys.stdout.write('\r' + ' ' * len(last_message) + '\r')
    sys.stdout.flush()

  async def run(self):
    """ Run the deep research process, yielding the status updates and the final novel manuscript"""
    novel_generator_trace_id = gen_trace_id()
    with trace("Novel Generator trace", trace_id=novel_generator_trace_id):
      print(f"\nView trace: https://platform.openai.com/traces/trace?trace_id={novel_generator_trace_id}\n")
      print("Starting novel generation\n")

      genre, title, num_pages, num_words, num_chapters, plot, max_tokens = await self.get_user_parameters()   
          
      print("\nAwesome, now we'll generate your novel!\n")

    done_event = asyncio.Event()
    loader_task = asyncio.create_task(self.show_loading_indicator(done_event))

    generated_novel = await self.generate_novel(genre, title, num_pages, num_words, num_chapters, plot, max_tokens)

    write_novel_to_file(generated_novel)

    # Signal that loading is done
    done_event.set()
    await loader_task  # Let it finish cleanly

  async def get_user_parameters(self):
    """Prompt the user for various novel parameters"""
    print("Getting user inputs\n")
    return get_user_inputs()

  async def generate_novel(self, genre, title, num_pages, num_words, num_chapters, plot, max_tokens):
    """Pass user input and generate the novel"""
    print("Generating the novel\n")
    return await generate_novel(genre, title, num_pages, num_words, num_chapters, plot, max_tokens)
  
  async def write_novel_to_file(self, novel_contents):
    write_novel_to_file(novel_contents) 