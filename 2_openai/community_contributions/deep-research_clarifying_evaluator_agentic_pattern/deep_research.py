from cProfile import label
from typing import Any
from dotenv import load_dotenv
from agents import RunContextWrapper, Runner, TContext, Tool, trace, gen_trace_id, RunHooks, Agent
import gradio as gr
from numpy import isin
from openai.types.responses import ResponseTextDeltaEvent
from research_manager import research_manager
import logging
import asyncio
import json

load_dotenv(override=True)

class DeepResearchHooks(RunHooks):
        async def on_agent_start(self, context: RunContextWrapper[TContext], agent: Agent) -> str:
            message = f"Agent {agent.name} started"
            print(message)

        async def on_tool_start(self, context: RunContextWrapper[TContext],
            agent: Agent[TContext],
            tool: Tool):
            message = f"Tool '{tool.name}' started with arguments: {context}"
            print(message)
            # return gr.update(value=message, elem_id="status")
            # yield f"Tool '{tool.name}' started with arguments: {context.input}"

        async def on_tool_end(self, context: RunContextWrapper[TContext],
            agent: Agent[TContext],
            tool: Tool,
            result: str):
            message = f"Tool '{tool.name}' ended with result: {result}"
            print(message)
            print(context)

        async def on_handoff(self, context: RunContextWrapper[TContext],
            from_agent: Agent[TContext],
            to_agent: Agent[TContext]):
            message = f"Handoff happened from '{from_agent.name}' to '{to_agent.name}'"
            print(message)
          
        async def on_agent_end(self, 
            context: RunContextWrapper[TContext],
            agent: Agent[TContext],
            output: Any) -> None:
            message = f"Agent '{agent.name}' processing completed."
            print(message)

hooks = DeepResearchHooks()

async def deep_research(*arguments: list[str]) -> str:
        args = list(arguments)
        query = args[0]
        state = args[1]
        args.remove(query)
        args.remove(state)
        clarifying_questions_responses = args
        clarifying_questions = []
        if state:
          clarifying_questions = state['clarifying_questions']
          if clarifying_questions != '':
            print(clarifying_questions_responses)
            print(clarifying_questions)
            for index, question in enumerate(clarifying_questions):
              print(index)
              question['user_response'] = clarifying_questions_responses[index]

        trace_id = gen_trace_id()
        with trace("Query Research trace", trace_id=trace_id):
            print(f"View trace: https://platform.openai.com/traces/trace?trace_id={trace_id}")
            print("Starting research...")
            try:    
                result = Runner.run_streamed(
                    starting_agent=research_manager,
                    input=f"Query: {query} and Clarifying Questions: {clarifying_questions}",
                    hooks=hooks
                )
                
                async for event in result.stream_events():
                  if event.type == "run_item_stream_event":
                        print(event.name)
                        if event.name == "tool_output":
                          print(event.item.agent.name)
                          print(event.item.raw_item)
                          print(event.item.raw_item['output'])
                          yield gr.update(), gr.update(value=f"Status: Processing {event.item.agent.name}...\n Output: {event.item.raw_item['output']}"), gr.update()
                  elif event.type != "raw_response_event":
                        yield gr.update(value=f"Event called: {event.type}", elem_id="report"), gr.update(value=f"Status: Processing {event.type}", elem_id="status"), gr.update()
                    
                final_result = result.final_output;
                
                print(f"FInal result: {final_result}")
                if hasattr(final_result, 'report'):
                  yield gr.update(value=json.dumps(final_result), elem_id="report"), gr.update(value="Status: Completed", elem_id="status"), gr.update()
                elif hasattr(final_result, 'clarifying_questions'):
                  list_of_dicts = [item.model_dump() for item in final_result.clarifying_questions]
                  json_string = json.dumps(list_of_dicts, indent=2)
                  yield gr.update(value="Answer clarifying questions"), gr.update(value="Status: Completed", elem_id="status"), gr.update(value=json_string)
                else:
                  print("Research Completed")
                  yield gr.update(final_result), gr.update("Status: Research Completed Successfully"), gr.update()

            except Exception as e:
                print(f"An error occurred: {e}")
                yield gr.update(value="An error occurred during research.", elem_id="report"), gr.update(value=f"Error: {e}", elem_id="status"), gr.update()
        
with gr.Blocks(theme=gr.themes.Citrus()) as chat_interface:
    state = gr.State({})
    gr.Markdown("Deep Research with Evaluation")
    query_text = gr.Textbox(label="What topic would you like to research?", elem_id="query_text")

    question_input = gr.Markdown(visible=False)

    dynamic_inputs = [query_text, state]
    @gr.render(inputs=[question_input, state])
    def render_question_inputs(clarifying_questions, current_state):
      clarifying_questions = json.loads(clarifying_questions)
      current_state["clarifying_questions"] = clarifying_questions
      gr.Markdown("Answer below questions to proceed further")
      for clarifying_question in clarifying_questions:
        input = gr.Textbox(label=clarifying_question['question'], placeholder=clarifying_question['reason'])
        dynamic_inputs.append(input)
      button.click(fn=deep_research, inputs=dynamic_inputs, outputs=[report, status, question_input])
      query_text.submit(fn=deep_research, inputs=dynamic_inputs, outputs=[report, status, question_input])


    button = gr.Button("Submit", variant='huggingface')
    gr.Markdown("Output")
    report = gr.Markdown(label="Report", elem_id="report")
    gr.Markdown("Status")
    status = gr.Markdown(label="Status", elem_id="status")

    print(dynamic_inputs)
    button.click(fn=deep_research, inputs=dynamic_inputs, outputs=[report, status, question_input])
    query_text.submit(fn=deep_research, inputs=dynamic_inputs, outputs=[report, status, question_input])
    chat_interface.launch()
