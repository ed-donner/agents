import gradio as gr
from agents import InputGuardrailTripwireTriggered, Runner, RunResult, trace
from build_agents import routing_agent


async def chat(message, history):
    # The history from Gradio with type="messages" can include extra keys.
    # We need to strip it down to just 'role' and 'content' for the agent.
    processed_history = [
        {"role": msg["role"], "content": msg["content"]} for msg in history
    ]
    current_input = processed_history + [{"role": "user", "content": message}]

    with trace(workflow_name="Coding tutor routing"):
        try:
            result: RunResult = await Runner.run(
                starting_agent=routing_agent,
                input=current_input,
            )
            # The agent's final output is a string, which can be returned directly.
            return result.final_output

        except InputGuardrailTripwireTriggered as e:
            print(f"INFO | {e}")
            # print(
            #     f"INFO | {e.guardrail_result.output.output_info['Found_Unexpected_Message'].clarification_message}"
            # )
            error_message = e.guardrail_result.output.output_info[
                "Found_Unexpected_Message"
            ].clarification_message
            return error_message


# Using Gradio | It will handle the chat history and UI components automatically
chatInterface = gr.ChatInterface(
    fn=chat,
    type="messages",
    title="Code Tutor",
    description="Ask me anything about Python, JavaScript, or SQL.",
    examples=[
        ["What is a decorator in Python?"],
        ["How does hoisting work in JavaScript?"],
        ["What are the different types of JOINs in SQL?"],
    ],
    theme="ocean",
)

if __name__ == "__main__":
    chatInterface.launch()
