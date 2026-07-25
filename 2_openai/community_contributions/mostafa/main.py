import gradio as gr
from research_manager import ResearchManager
from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env file
manager = ResearchManager()
clarity_rounds = 0


async def stream_research(query, state):
    ''' Yields updates during the research process. '''
    async for item in manager.run_research(query):
        if item.get('type') == 'status':
            # Update only the markdown in the initial panel
            yield (
                gr.update(value=item['content']),  # initial output
                gr.update(),            # questions box (no change)
                gr.update(),            # answer panel (no change)
                gr.update(),            # answer output (no change)
                gr.update(),            # initial panel visibility (no change)
                gr.update(),            # answer panel visibility (no change)
                state
            )
        else:
            # Final report, hide the answer panel, show the initial panel, and clear questions/answers
            yield (
                # initial output with final report
                gr.update(value=item['content']),
                gr.update(),                       # questions box (clear)
                gr.update(''),            # answer output (clear)
                gr.update(),                       # answer output (clear)
                gr.update(visible=True),           # Show the initial panel
                gr.update(visible=False),          # Hide the answer panel
                None                               # Clear state after research is done
            )
            break  # End the generator after yielding the final result


async def first_step(query, state):
    ''' Handle initial query submission. '''
    global clarity_rounds

    clarity = await manager.clarify_query(query)
    if clarity.is_clear:
        # Clear - stream research
        yield (
                gr.update(),        # initial output (no change, will be updated during streaming)
                gr.update(),                       # questions box (no change)
                gr.update(''),            # answer input (clear) 
                gr.update(''),            # answer output (clear)
                gr.update(visible=True),           # Show the initial panel
                gr.update(visible=False),          # Hide the answer panel
                state                             
        )
        async for update in stream_research(query, state):
            yield update
    else:
        # Not clear, show answer panel with questions
        new_state = {
            'original_query': query,
            'refined': clarity.refined_query,
            'answers': [],  # Store answers in state for potential future rounds
        }

        questions_text = '\n'.join(
            [f'{i+1}. {q}' for i, q in enumerate(clarity.questions)]
        )

        # Show answer panel with questions, hide initial panel
        yield (
            gr.update(),                        # initial output (no change)
            gr.update(value=questions_text),    # questions box (update with questions)
            gr.update(value=''),                # answer input (clear)
            gr.update(value=''),                # answer output (clear)
            gr.update(visible=False),           # hide initial panel
            gr.update(visible=True),            # show answer panel
            new_state
        )


async def second_step(answers, state):
    ''' Handel answers submission. Re-run clarifier and either continue or start research. '''
    global clarity_rounds

    session_error = 'Error: No previous state found. Please start a new research query.'

    if not state:
        yield (
            # initial output with error message
            gr.update(value=session_error),
            gr.update(),                        # questions box (no change)
            gr.update(),                        # answer panel (no change)
            gr.update(),                        # answer output (no change)
            gr.update(visible=True),            # Show the initial panel
            gr.update(visible=False),           # Hide the answer panel
            None,                               # Clear state
        )
        return

    # Combine previous context with new answers
    base = state.get('refined', state['original_query'])
    combined = f'{base}\n\nAdditional context\n{answers}'

    # Run clarification again
    clarity = await manager.clarify_query(combined)
    clarity_rounds += 1

    while not clarity.is_clear and clarity_rounds <= manager.extra_clarity_rounds:
        # still not clear, ask more Questions
        new_state = {
            'original_query': state['original_query'],
            'refined': clarity.refined_query or state['refined'],
            'answers': [],
        }
        questions_text = '\n'.join(
            [f'{i+1}. {q}' for i, q in enumerate(clarity.questions)]
        )
        yield (
            gr.update(),                       # initial output (no change)
            gr.update(value=questions_text),   # questions box (update with new questions)
            gr.update(value=''),               # answer input (clear) for next round
            gr.update(),                       # answer output (no change)
            gr.update(visible=False),          # keep initial panel hidden 
            gr.update(visible=True),           # Show the answer panel 
            new_state
        )
    else:
        # Clear - stream Research
        final_query = clarity.refined_query or combined
        # Show initial panel and hide answer panel while streaming results
        yield (
            gr.update(),                       # initial output (no change, will be updated during streaming)
            gr.update(),                       # questions box (no change)
            gr.update(value=''),               # answer input (clear)
            gr.update(value=''),               # answer output (clear)
            gr.update(visible=True),           # Show the initial panel
            gr.update(visible=False),          # Hide the answer panel
            state        
        )
        async for update in stream_research(final_query, state):
            yield update


with gr.Blocks() as app:
    # stores {'original_query': str, 'questions': List[str], 'refined': str}
    state = gr.State({'original': '', 'refined': '', 'answers': []})

    # Panels
    initial_panel = gr.Group(visible=True)
    answer_panel = gr.Group(visible=False)

    with initial_panel:
        query_input = gr.Textbox(label="Research Query")
        submit_btn = gr.Button("Start Research")
        initial_output = gr.Markdown()

    with answer_panel:
        questions_box = gr.Markdown()
        answers_box = gr.Textbox(
            label="Your Answers", placeholder="Provide answers, one per line or in a paragraph")
        answer_btn = gr.Button("Submit Answers")
        answer_output = gr.Markdown()

    outputs = [
        initial_output,  # Markdown in initial panel
        questions_box,   # Markdown in answer panel for questions
        answers_box,     # Textbox in answer panel for user answers
        answer_output,   # Markdown in answer panel for any feedback or errors
        initial_panel,   # Visibility control for initial panel
        answer_panel,    # Visibility control for answer panel
        state,           # State to pass between steps
    ]

    # Event handlers
    submit_btn.click(
        fn=first_step,
        inputs=[query_input, state],
        outputs=outputs,
        concurrency_limit=None
    )

    answer_btn.click(
        fn=second_step,
        inputs=[answers_box, state],
        outputs=outputs,
        concurrency_limit=None
    )

app.launch(inbrowser=True)
