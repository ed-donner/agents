import time
import random
import gradio as gr
from pydantic import BaseModel
from queue import Queue

from engineering_team_using_flow.main import EngineeringFlow
from engineering_team_using_flow.shared_queue import (
    TaskInfo,
    shared_task_output_queue,
    add_to_queue,
)


def generate_random_statement():
    return f"{random.choice(['The cat', 'A dog', 'My friend'])} {random.choice(['eats', 'jumps', 'reads'])} {random.choice(['a book.', 'the newspaper.', 'some food.'])} {random.choice(['quickly', 'happily', 'silently'])}"


def start_long_running_process():
    print("🚀 Long Running process started")
    for i in range(10):
        time.sleep(1)
        task_type = random.choice(["markdown", "code"])
        add_to_queue(
            TaskInfo(
                name=f"Task {i}",
                type=task_type,
                output=(
                    f"\nprint('task {i}')"
                    if task_type == "code"
                    else generate_random_statement()
                ),
            )
        )
    add_to_queue(TaskInfo(name="Complete", type="markdown", output="✅ Done."))
    print("✅ Long Running process Finished")


def run_and_stream(module_name: str, requirements: str):
    print("🚀 Background process started")
    if module_name.strip() == "" or requirements.strip() == "":
        yield [{"role" : "assistant", "content" : "### Mandatory fields missing ..."}]
        return

    # Start the process in a thread so we can yield live
    from threading import Thread

    thread = Thread(target=EngineeringFlow(module_name, requirements).kickoff)
    thread.start()

    print("🚀 Monitoring queue ...")
    messages = []
    curr_role = "user"
    while thread.is_alive() or not shared_task_output_queue.empty():
        if not shared_task_output_queue.empty():
            task = shared_task_output_queue.get()
            print(f"🧲 {task.name} - {task.output}")

            curr_role = "assistant" if curr_role == "user" else "user"
            messages.append(
                {
                    "role": curr_role,
                    "content": "",
                }
            )

            for char in f"{task.output}":
                time.sleep(0.005)
                messages[-1]["content"] += char
                yield messages

        else:
            time.sleep(0.2)  # small delay to prevent CPU spin
    
    curr_role = "assistant" if curr_role == "user" else "user"
    messages.append({"role":curr_role, "content" : "# All Done!"})
    yield(messages)

# UI
with gr.Blocks(theme=gr.themes.Ocean()) as demo:
    module_name = gr.Textbox(
        label="Module Name", placeholder="What do you want to call your product?"
    )
    requirements = gr.Textbox(
        label="Business Requirements",
        placeholder="I want to build a ... Clearly state your business requirements.",
    )
    run_button = gr.Button("Create Product", variant="primary")
    chat = gr.Chatbot(type="messages", label="Crew Output", height=600)
    run_button.click(
        fn=run_and_stream, inputs=[module_name, requirements], outputs=chat
    )

demo.launch()
