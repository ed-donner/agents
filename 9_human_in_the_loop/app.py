"""
Week 9 App — Human-in-the-Loop Gradio UI
Watch an agent plan steps, approve/reject each one in real time.
Run: python app.py
"""

import threading
import queue
import time
from dotenv import load_dotenv
import gradio as gr
from openai import OpenAI
from hitl import Step, ApprovalGate, ApprovalResult, Decision, HITLAgent, FeedbackStore

load_dotenv(override=True)
client = OpenAI()

# Queues for async communication between agent thread and UI
request_q: queue.Queue = queue.Queue()   # agent → UI: step needing approval
response_q: queue.Queue = queue.Queue()  # UI → agent: human decision

WORKFLOW_STEPS = [
    Step("research",   "Research the topic and list 5 key facts.",                    confidence=0.95),
    Step("outline",    "Create a 5-section outline based on the research.",            confidence=0.80),
    Step("draft",      "Write a 200-word first draft of the content.",                confidence=0.70),
    Step("fact_check", "Verify all factual claims in the draft.",                      confidence=0.55, cost_estimate_usd=0.08),
    Step("publish",    "Finalize and publish the content to the website.",             confidence=0.40, cost_estimate_usd=2.50),
]


def make_callback_gate():
    """Return a gate that uses queues for UI integration."""
    def callback(step: Step) -> ApprovalResult:
        request_q.put(step)
        result = response_q.get(timeout=300)
        return result

    return ApprovalGate(backend="callback", callback=callback, confidence_threshold=0.75, cost_threshold_usd=0.05)


def run_agent_thread(topic: str, log_list: list):
    """Runs in background thread. Executes the agent workflow."""
    gate = make_callback_gate()
    feedback_store = FeedbackStore()
    agent = HITLAgent(gate=gate, feedback_store=feedback_store)

    def executor(step: Step, feedback_ctx: str) -> str:
        msgs = [{"role": "system", "content": "You are a helpful content assistant. Be concise."}]
        if feedback_ctx:
            msgs.append({"role": "user", "content": f"Human feedback from earlier steps:\n{feedback_ctx}"})
        msgs.append({"role": "user", "content": f"Topic: {topic}\n\nTask: {step.description}"})
        resp = client.chat.completions.create(model="gpt-4o-mini", messages=msgs, max_tokens=300)
        return resp.choices[0].message.content

    results = agent.run(WORKFLOW_STEPS, executor)
    log_list.extend(results)
    request_q.put(None)  # signal done


current_step_info = {}
agent_log = []


def start_workflow(topic: str):
    agent_log.clear()
    request_q.queue.clear()
    response_q.queue.clear()
    current_step_info.clear()

    t = threading.Thread(target=run_agent_thread, args=(topic, agent_log), daemon=True)
    t.start()
    return f"Workflow started for topic: '{topic}'\nWaiting for first step approval...", "", "", ""


def poll_for_step():
    """Check if agent is waiting for approval."""
    try:
        step = request_q.get_nowait()
    except queue.Empty:
        return gr.update(), gr.update(), gr.update(), gr.update()

    if step is None:
        summary = "\n\n".join(
            f"[{r['step']}] {r['decision'].upper()}\n{r['result'] or ''}"
            for r in agent_log
        )
        return "✅ Workflow complete!", "", "", summary

    current_step_info["step"] = step
    details = (
        f"**Step: {step.name}**\n\n"
        f"{step.description}\n\n"
        f"Confidence: {step.confidence:.0%} | "
        f"Est. cost: ${step.cost_estimate_usd:.4f}"
    )
    return details, "", "Approve, reject, or provide feedback below.", gr.update()


def approve_step(feedback: str):
    step = current_step_info.get("step")
    if not step:
        return "No pending step.", ""
    response_q.put(ApprovalResult(Decision.APPROVE, feedback=feedback))
    return f"✅ Approved: {step.name}", ""


def reject_step(reason: str):
    step = current_step_info.get("step")
    if not step:
        return "No pending step.", ""
    response_q.put(ApprovalResult(Decision.REJECT, feedback=reason))
    return f"❌ Rejected: {step.name} — {reason}", ""


with gr.Blocks(title="Week 9 — Human-in-the-Loop") as demo:
    gr.Markdown("# Week 9: Human-in-the-Loop\nThe agent pauses at each step. You approve or reject before it proceeds.")

    with gr.Row():
        topic_input = gr.Textbox(label="Content topic", value="The future of AI agents in enterprise", scale=4)
        start_btn = gr.Button("Start workflow", variant="primary", scale=1)

    status_box = gr.Textbox(label="Status", lines=2)

    with gr.Row():
        step_box = gr.Markdown(label="Current step")
        hint_box = gr.Textbox(label="Hint", lines=1, interactive=False)

    feedback_input = gr.Textbox(label="Feedback / rejection reason (optional)")

    with gr.Row():
        approve_btn = gr.Button("✅ Approve", variant="primary")
        reject_btn = gr.Button("❌ Reject", variant="stop")

    poll_btn = gr.Button("🔄 Check for next step", variant="secondary")
    log_box = gr.Textbox(label="Completed steps", lines=15)

    start_btn.click(start_workflow, inputs=[topic_input], outputs=[status_box, step_box, hint_box, log_box])
    poll_btn.click(poll_for_step, outputs=[step_box, feedback_input, hint_box, log_box])
    approve_btn.click(approve_step, inputs=[feedback_input], outputs=[status_box, feedback_input])
    reject_btn.click(reject_step, inputs=[feedback_input], outputs=[status_box, feedback_input])

if __name__ == "__main__":
    demo.launch()
