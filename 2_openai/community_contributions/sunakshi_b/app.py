import gradio as gr
import asyncio
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

project_root = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(project_root))
load_dotenv(override=True)

from agents import Runner, gen_trace_id
from coordinator_agent import IntakeCoordinatorAgent
from teacher_agent import SocraticTeacherAgent

class TeacherAppManager:
    def __init__(self):
        self.coordinator = IntakeCoordinatorAgent()
        self.teacher = SocraticTeacherAgent()
        self.reset()
        
    def reset(self):
        self.current_stage = "intake"
        self.intake_history = []
        self.teacher_history = []
        self.trace_id = gen_trace_id()
        self.context_summary = ""

    async def process_message(self, user_message: str):
        if self.current_stage == "intake":
            return await self._handle_intake(user_message)
        elif self.current_stage == "teaching":
            return await self._handle_teaching(user_message)

    async def _handle_intake(self, user_message: str):
        print(f"[Intake Coordinator] Processing: {user_message}")
        conversation = self.intake_history + [{"role": "user", "content": user_message}]
        
        result = await Runner.run(self.coordinator, conversation)
        response = str(result.final_output)
        
        self.intake_history.append({"role": "user", "content": user_message})
        self.intake_history.append({"role": "assistant", "content": response})
        
        if "READY_FOR_TEACHER" in response:
            self.current_stage = "teaching"
            print("[System] Transitioning to Socratic Teacher")
            response = response.replace("READY_FOR_TEACHER", "").strip()
            self.context_summary = response
            
        return response

    async def _handle_teaching(self, user_message: str):
        print(f"[Socratic Teacher] Processing: {user_message}")
        
        if not self.teacher_history and self.context_summary:
            self.teacher_history = [
                {"role": "system", "content": f"The intake is complete. Here is the context:\n\n{self.context_summary}\n\nPlease begin your Socratic teaching session now."}
            ]
            
        conversation = self.teacher_history + [{"role": "user", "content": user_message}]
        
        result = await Runner.run(self.teacher, conversation)
        response = str(result.final_output)
        
        self.teacher_history.append({"role": "user", "content": user_message})
        self.teacher_history.append({"role": "assistant", "content": response})
        
        return response

manager = TeacherAppManager()

async def chat_async(message, history):
    if not message.strip():
        return history
    
    stage_before = manager.current_stage
    response = await manager.process_message(message)
    
    speaker = "Coordinator" if stage_before == "intake" else "Teacher"
    
    history.append({"role": "user", "content": message, "metadata": {"title": "👤 Student"}})
    history.append({"role": "assistant", "content": response, "metadata": {"title": f"🎓 {speaker}"}})
    
    return history

def chat(message, history):
    return asyncio.run(chat_async(message, history))

with gr.Blocks(title="Teacher Q&A Hub", theme=gr.themes.Soft()) as demo:
    gr.Markdown("# 👩‍🏫 Interactive Teacher Q&A\n\nWelcome! Let's learn something new today. The Intake Coordinator will get you started.")
    
    with gr.Row():
        with gr.Column(scale=3):
            chatbot = gr.Chatbot(height=500, type="messages")
            msg = gr.Textbox(label="Your Message", placeholder="Type your response here...")
            with gr.Row():
                submit = gr.Button("Send", variant="primary")
                clear = gr.Button("Start New Topic", variant="secondary")
        
        with gr.Column(scale=1):
            status_display = gr.Markdown("### Current Stage\n- 🔵 Intake Phase\n- ⏳ Teaching Phase")

    def get_status_markdown():
        if manager.current_stage == "intake":
            return "### Current Stage\n- 🔵 **Intake Phase** (Active)\n- ⏳ Teaching Phase"
        else:
            return "### Current Stage\n- ✅ Intake Phase (Complete)\n- 🔵 **Teaching Phase** (Active)"

    def submit_message(message, history):
        return chat(message, history), "", get_status_markdown()

    submit.click(submit_message, inputs=[msg, chatbot], outputs=[chatbot, msg, status_display])
    msg.submit(submit_message, inputs=[msg, chatbot], outputs=[chatbot, msg, status_display])

    def reset_and_update():
        manager.reset()
        return [], "", get_status_markdown()
        
    clear.click(reset_and_update, outputs=[chatbot, msg, status_display])

if __name__ == "__main__":
    if not os.environ.get("OPENAI_API_KEY"):
        print("Please set your OPENAI_API_KEY environment variable.")
        sys.exit(1)
    demo.launch(inbrowser=True)
