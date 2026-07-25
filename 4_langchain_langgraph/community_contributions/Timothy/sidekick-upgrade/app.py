import gradio as gr
from sidekick import Sidekick
import asyncio

async def setup():
	sidekick = Sidekick()
	await sidekick.setup()
	return sidekick


async def process_message(sidekick, message, success_criteria, history, clarifying_answers):
	if sidekick is None:
		
		return history, sidekick, ""
	results = await sidekick.run_superstep(message, success_criteria, history, clarifying_answers)
	# Check for clarifying questions in the latest state
	# We'll extract clarifying questions from the sidekick's memory
	clarifying_question = ""
	try:
		# Try to get the latest state from memory
		state = sidekick.memory.load(sidekick.sidekick_id, "state")
		if state and state.get("clarifying_questions") and len(state["clarifying_answers"] or []) < len(state["clarifying_questions"] or []):
			next_idx = len(state["clarifying_answers"] or [])
			clarifying_question = state["clarifying_questions"][next_idx]
	except Exception as e:
		print(f"Error retrieving clarifying question: {e}")
	return results, sidekick, clarifying_question


async def answer_clarifying(sidekick, message, success_criteria, history, clarifying_answers, clarifying_input):
	if sidekick is None:
		
		return history, sidekick, clarifying_answers, ""
	clarifying_answers = clarifying_answers or []
	clarifying_answers.append(clarifying_input)
	results = await sidekick.run_superstep(message, success_criteria, history, clarifying_answers)
	# Check for next clarifying question
	clarifying_question = ""
	try:
		state = sidekick.memory.load(sidekick.sidekick_id, "state")
		if state and state.get("clarifying_questions") and len(state["clarifying_answers"] or []) < len(state["clarifying_questions"] or []):
			next_idx = len(state["clarifying_answers"] or [])
			clarifying_question = state["clarifying_questions"][next_idx]
	except Exception as e:
		print(f"Error retrieving clarifying question: {e}")
	return results, sidekick, clarifying_answers, clarifying_question

async def reset():
	new_sidekick = Sidekick()
	await new_sidekick.setup()
	return "", "", None, new_sidekick, [], ""

def free_resources(sidekick):
	print("Cleaning up")
	try:
		if sidekick:
			sidekick.cleanup()
	except Exception as e:
		print(f"Exception during cleanup: {e}")
  


with gr.Blocks(title="Sidekick (Timothy)", theme=gr.themes.Default(primary_hue="emerald")) as ui:
	gr.Markdown("## Sidekick Personal Co-Worker ")
	sidekick = gr.State(delete_callback=free_resources)
	clarifying_answers = gr.State([])
	clarifying_question = gr.State("")

	with gr.Row():
		chatbot = gr.Chatbot(label="Sidekick", height=300, type="messages")
	with gr.Group():
		with gr.Row():
			message = gr.Textbox(show_label=False, placeholder="Your request to the Sidekick")
		with gr.Row():
			success_criteria = gr.Textbox(
				show_label=False, placeholder="What are your success critiera?"
			)
	with gr.Row():
		clarifying_display = gr.Markdown(visible=False)
		clarifying_input = gr.Textbox(show_label=False, placeholder="Answer clarifying question (if any)")
	with gr.Row():
		reset_button = gr.Button("Reset", variant="stop")
		go_button = gr.Button("Go!", variant="primary")

	ui.load(setup, [], [sidekick])

	def show_clarifying(clarifying_question):
		if clarifying_question:
			return gr.update(visible=True, value=f"**Clarifying question:** {clarifying_question}"), gr.update(visible=True)
		else:
			return gr.update(visible=False, value=""), gr.update(visible=False)

	# When a message is submitted, process and check for clarifying question
	message.submit(
		process_message,
		[sidekick, message, success_criteria, chatbot, clarifying_answers],
		[chatbot, sidekick, clarifying_question],
	).then(
		show_clarifying, [clarifying_question], [clarifying_display, clarifying_input]
	)
	success_criteria.submit(
		process_message,
		[sidekick, message, success_criteria, chatbot, clarifying_answers],
		[chatbot, sidekick, clarifying_question],
	).then(
		show_clarifying, [clarifying_question], [clarifying_display, clarifying_input]
	)
	go_button.click(
		process_message,
		[sidekick, message, success_criteria, chatbot, clarifying_answers],
		[chatbot, sidekick, clarifying_question],
	).then(
		show_clarifying, [clarifying_question], [clarifying_display, clarifying_input]
	)
	clarifying_input.submit(
		answer_clarifying,
		[sidekick, message, success_criteria, chatbot, clarifying_answers, clarifying_input],
		[chatbot, sidekick, clarifying_answers, clarifying_question],
	).then(
		show_clarifying, [clarifying_question], [clarifying_display, clarifying_input]
	)
	reset_button.click(reset, [], [message, success_criteria, chatbot, sidekick, clarifying_answers, clarifying_input])

ui.launch()