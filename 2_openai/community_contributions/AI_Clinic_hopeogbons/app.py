import gradio as gr
import asyncio
from agents import Runner, trace, gen_trace_id
from triage_nurse_agent import TriageNurseAgent
from resident_physician_agent import ResidentPhysicianAgent
from chief_physician_agent import ChiefPhysicianAgent
from dotenv import load_dotenv

load_dotenv(override=True)


class AIClinicManager:
    """
    Manages the conversation flow through the AI Clinic multi-agent system.
    """
    
    def __init__(self):
        self.triage_nurse = TriageNurseAgent()
        self.resident_physician = ResidentPhysicianAgent()
        self.chief_physician = ChiefPhysicianAgent()
        self.reset()
    
    def reset(self):
        """Reset the conversation state"""
        self.current_stage = "triage"
        self.triage_data = None
        self.resident_data = None
        self.chief_data = None
        self.specialist_results = None
        self.trace_id = gen_trace_id()
        self.triage_history = []
        self.resident_history = []
        self.chief_history = []
        
    async def process_message(self, user_message: str):
        """
        Process a user message through the appropriate agent based on current stage.
        Returns the agent's response and updates state accordingly.
        """
        
        if self.current_stage == "triage":
            return await self._handle_triage(user_message)
        
        elif self.current_stage == "resident":
            return await self._handle_resident(user_message)
        
        elif self.current_stage == "chief":
            return await self._handle_chief(user_message)
        
        elif self.current_stage == "results_ready":
            return await self._handle_results_delivery(user_message)
        
        elif self.current_stage == "complete":
            return "Thank you for using AI Clinic. Your consultation is now complete. If you have any questions about your assessment, please consult with a licensed healthcare provider. You can start a new consultation by clicking 'Start New Consultation'."
    
    async def _handle_triage(self, user_message: str):
        """Handle triage nurse interaction"""
        print(f"[Triage Nurse] Processing: {user_message}")
        
        conversation = self.triage_history + [{"role": "user", "content": user_message}]
        
        result = await Runner.run(
            self.triage_nurse,
            conversation
        )
        
        response = str(result.final_output)
        
        self.triage_history.append({"role": "user", "content": user_message})
        self.triage_history.append({"role": "assistant", "content": response})
        
        if "READY_FOR_RESIDENT_PHYSICIAN" in response:
            self.current_stage = "resident"
            print(f"[System] Transitioning to Resident Physician")
            self.triage_data = {"conversation": self.triage_history}
            response = response.replace("READY_FOR_RESIDENT_PHYSICIAN", "").strip()
        
        return response
    
    async def _handle_resident(self, user_message: str):
        """Handle resident physician interaction"""
        print(f"[Resident Physician] Processing: {user_message}")
        
        if not self.resident_history and self.triage_data:
            triage_conv = self.triage_data.get("conversation", [])
            if triage_conv:
                triage_summary = "TRIAGE NURSE SUMMARY:\n"
                for msg in triage_conv:
                    triage_summary += f"{msg['role'].upper()}: {msg['content']}\n"
                
                self.resident_history = [
                    {"role": "system", "content": f"You are receiving a patient from the triage nurse. Here is the conversation so far:\n\n{triage_summary}\n\nPlease proceed with your assessment based on this information."}
                ]
        
        conversation = self.resident_history + [{"role": "user", "content": user_message}]
        
        result = await Runner.run(
            self.resident_physician,
            conversation
        )
        
        response = str(result.final_output)
        
        self.resident_history.append({"role": "user", "content": user_message})
        self.resident_history.append({"role": "assistant", "content": response})
        
        if "READY_FOR_CHIEF_PHYSICIAN" in response:
            self.current_stage = "chief"
            print(f"[System] Transitioning to Chief Physician")
            self.resident_data = {"conversation": self.resident_history}
            response = response.replace("READY_FOR_CHIEF_PHYSICIAN", "").strip()
        
        return response
    
    async def _handle_chief(self, user_message: str):
        """Handle Chief Physician conversation and specialist consultation"""
        print(f"[Chief Physician] Processing: {user_message}")
        
        if not self.chief_history:
            triage_conv = self.triage_data.get("conversation", []) if self.triage_data else []
            resident_conv = self.resident_data.get("conversation", []) if self.resident_data else []
            
            case_summary = "COMPLETE PATIENT CASE:\n\n"
            
            if triage_conv:
                case_summary += "TRIAGE NURSE CONVERSATION:\n"
                for msg in triage_conv:
                    case_summary += f"{msg['role'].upper()}: {msg['content']}\n"
                case_summary += "\n"
            
            if resident_conv:
                case_summary += "RESIDENT PHYSICIAN CONVERSATION:\n"
                for msg in resident_conv:
                    content = msg['content'].replace("**Resident Physician:** ", "")
                    case_summary += f"{msg['role'].upper()}: {content}\n"
            
            from config import CHIEF_PHYSICIAN_NAME, RESIDENT_PHYSICIAN_NAME
            
            self.chief_history = [
                {"role": "system", "content": f"""You are {CHIEF_PHYSICIAN_NAME}, the Chief Physician. 
                
You are receiving a patient from {RESIDENT_PHYSICIAN_NAME} (Resident Physician). Here is the complete case:

{case_summary}

Your role:
1. Introduce yourself warmly to the patient
2. Explain that you'd like to consult with three specialists (Emergency, Medicine, Surgery)
3. Ask for their permission to proceed
4. If they agree, use the phrase "READY_FOR_SPECIALIST_CONSULTATION" to signal you're ready to consult
5. Be conversational, empathetic, and professional

Do NOT consult the specialists yet - just have a conversation with the patient and get their consent."""}
            ]
        
        conversation = self.chief_history + [{"role": "user", "content": user_message}]
        
        result = await Runner.run(
            self.chief_physician,
            conversation
        )
        
        response = str(result.final_output)
        
        if "READY_FOR_SPECIALIST_CONSULTATION" in response:
            print(f"[System] Chief Physician consulting with specialists...")
            
            clean_response = response.replace("READY_FOR_SPECIALIST_CONSULTATION", "").strip()
            
            self.chief_history.append({"role": "user", "content": user_message})
            self.chief_history.append({"role": "assistant", "content": clean_response})
            
            self.specialist_results = await self._run_specialist_consultation()
            
            results_prompt = "The specialist consultations are complete. Tell the patient in a warm, playful way that their results are ready and ask when they'd like to hear them. Be creative but professional."
            
            conversation = self.chief_history + [{"role": "user", "content": results_prompt}]
            
            result = await Runner.run(
                self.chief_physician,
                conversation
            )
            results_ready_msg = str(result.final_output)
            
            self.chief_history.append({"role": "user", "content": results_prompt})
            self.chief_history.append({"role": "assistant", "content": results_ready_msg})
            
            response = clean_response + "\n\n" + results_ready_msg
            self.current_stage = "results_ready"
        else:
            self.chief_history.append({"role": "user", "content": user_message})
            self.chief_history.append({"role": "assistant", "content": response})
        
        return response
    
    async def _handle_results_delivery(self, user_message: str):
        """Handle delivering results after patient is ready"""
        user_input = user_message.strip().lower()
        
        ready_keywords = [
            "yes", "ready", "ok", "okay", "sure", "go ahead", "please", 
            "show", "tell", "see", "hear", "share", "give", "let me",
            "come on", "now", "waiting", "proceed", "continue"
        ]
        
        if any(keyword in user_input for keyword in ready_keywords):
            print(f"[System] Delivering specialist results...")
            self.current_stage = "complete"
            return self.specialist_results
        else:
            reassurance_prompt = f"The patient responded with: '{user_message}'. They seem hesitant about hearing the results. Reassure them warmly and encourage them to hear the findings when ready. Be empathetic and understanding."
            
            conversation = self.chief_history + [{"role": "user", "content": reassurance_prompt}]
            
            result = await Runner.run(
                self.chief_physician,
                conversation
            )
            return str(result.final_output)
    
    async def _run_specialist_consultation(self):
        """Handle chief physician specialist consultation"""
        triage_conv = self.triage_data.get("conversation", []) if self.triage_data else []
        resident_conv = self.resident_data.get("conversation", []) if self.resident_data else []
        
        triage_summary = "\n".join([f"{msg['role'].upper()}: {msg['content']}" for msg in triage_conv]) if triage_conv else "No triage data"
        resident_summary = "\n".join([f"{msg['role'].upper()}: {msg['content']}" for msg in resident_conv]) if resident_conv else "No resident data"
        
        context = f"""
PATIENT CASE SUMMARY:

TRIAGE NURSE CONVERSATION:
{triage_summary}

RESIDENT PHYSICIAN CONVERSATION:
{resident_summary}

INSTRUCTIONS: You must NOW consult with ALL THREE specialists using your available tools:
- Call emergency_specialist tool
- Call medicine_specialist tool  
- Call surgery_specialist tool

After receiving all three specialist reports, synthesize their findings and present your comprehensive 
medical assessment following the format in your instructions.
"""
        
        result = await Runner.run(
            self.chief_physician,
            context
        )
        
        response = str(result.final_output)
        
        response += "\n\n---\n\n"
        response += "*⚠️ This is an AI-assisted assessment for educational purposes only. "
        response += "For actual medical concerns, please consult with licensed healthcare professionals.*\n\n"
        response += f"📊 [View Consultation Trace](https://platform.openai.com/traces/trace?trace_id={self.trace_id})"
        
        return response


# Global manager instance
manager = AIClinicManager()


async def chat_async(message, history):
    """Async chat function for Gradio"""
    if not message.strip():
        return history
    
    stage_before = manager.current_stage
    
    response = await manager.process_message(message)
    
    if stage_before == "triage":
        speaker = "Triage Nurse"
    elif stage_before == "resident":
        speaker = "Resident Physician"
    elif stage_before == "chief" or stage_before == "results_ready":
        speaker = "Chief Physician"
    elif stage_before == "complete":
        speaker = "AI Clinic"
    else:
        speaker = "AI Clinic"
    
    response = response.replace("**Triage Nurse:** ", "")
    response = response.replace("**Resident Physician:** ", "")
    response = response.replace("**Chief Physician:** ", "")
    
    history.append({
        "role": "user",
        "content": message,
        "metadata": {"title": "👤 Patient"}
    })
    history.append({
        "role": "assistant", 
        "content": response,
        "metadata": {"title": f"🩺 {speaker}"}
    })
    
    return history


def chat(message, history):
    """Sync wrapper for Gradio chat"""
    return asyncio.run(chat_async(message, history))


# Create Gradio interface
with gr.Blocks(title="AI Clinic - Medical Consultation", theme=gr.themes.Soft()) as demo:
    gr.Markdown("""
    # 🏥 AI Clinic - Multi-Agent Medical Consultation System
    
    Welcome! This is a multi-agent AI diagnostic system that will help assess your medical concerns.
    
    **How it works:**
    1. **Triage Nurse** - Welcomes you and collects your initial complaint
    2. **Resident Physician** - Asks follow-up questions and researches your symptoms
    3. **Chief Physician** - Consults with three specialists (Emergency, Medicine, Surgery) for a comprehensive assessment
    
    **⚠️ Disclaimer:** This is an AI demonstration system for educational purposes only. 
    It is NOT a substitute for professional medical advice, diagnosis, or treatment.
    """)
    
    with gr.Row():
        with gr.Column(scale=3):
            chatbot = gr.Chatbot(
                label="Consultation Chat",
                height=600,
                show_label=True,
                type="messages"
            )
            msg = gr.Textbox(
                label="Your Message",
                placeholder="Describe your symptoms or answer the doctor's questions...",
                lines=1,
                max_lines=1
            )
            with gr.Row():
                submit = gr.Button("Send", variant="primary")
                clear = gr.Button("Start New Consultation", variant="secondary")
        
        with gr.Column(scale=1):
            status_display = gr.Markdown("""
            ### 📋 Current Stage
            The system will guide you through:
            - 🔵 Triage (Starting...)
            - ⏳ Resident Assessment
            - ⏳ Specialist Consultation
            
            ### 💡 Tips
            - Be specific about symptoms
            - Mention duration and severity
            - Answer all questions honestly
            
            ### 🔗 Resources
            Track the AI's reasoning process using the trace URL provided at the end.
            """)
    
    def get_status_markdown():
        """Generate status markdown based on current stage"""
        stage = manager.current_stage
        
        if stage == "triage":
            stages_text = """- 🔵 **Triage** (In Progress...)
- ⏳ Resident Assessment
- ⏳ Specialist Consultation"""
        elif stage == "resident":
            stages_text = """- ✅ Triage (Complete)
- 🔵 **Resident Assessment** (In Progress...)
- ⏳ Specialist Consultation"""
        elif stage == "chief":
            stages_text = """- ✅ Triage (Complete)
- ✅ Resident Assessment (Complete)
- 🔵 **Specialist Consultation** (In Progress...)"""
        elif stage == "results_ready":
            stages_text = """- ✅ Triage (Complete)
- ✅ Resident Assessment (Complete)
- 🔵 **Specialist Consultation** (Results Ready!)"""
        elif stage == "complete":
            stages_text = """- ✅ Triage (Complete)
- ✅ Resident Assessment (Complete)
- ✅ **Specialist Consultation** (Complete)"""
        else:
            stages_text = """- ✅ Triage (Complete)
- ✅ Resident Assessment (Complete)
- ✅ Specialist Consultation (Complete)"""
        
        return f"""
### 📋 Current Stage
The system will guide you through:
{stages_text}

### 💡 Tips
- Be specific about symptoms
- Mention duration and severity
- Answer all questions honestly

### 🔗 Resources
Track the AI's reasoning process using the trace URL provided at the end.
"""
    
    def submit_message(message, history):
        """Handle message submission"""
        return chat(message, history), "", get_status_markdown()
    
    submit.click(
        submit_message,
        inputs=[msg, chatbot],
        outputs=[chatbot, msg, status_display]
    )
    
    msg.submit(
        submit_message,
        inputs=[msg, chatbot],
        outputs=[chatbot, msg, status_display]
    )
    
    def reset_and_update():
        """Reset conversation and update status"""
        manager.reset()
        return [], "", get_status_markdown()
    
    clear.click(
        reset_and_update,
        outputs=[chatbot, msg, status_display]
    )


if __name__ == "__main__":
    print("Starting AI Clinic Medical Consultation System...")
    print(f"Access the application at: http://localhost:7860")
    demo.launch(share=False, server_name="0.0.0.0", server_port=7860)

