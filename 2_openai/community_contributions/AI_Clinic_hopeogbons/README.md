# 🏥 AI Clinic - Multi-Agent Medical Consultation System

A sophisticated multi-agent AI diagnostic system that simulates a comprehensive medical consultation process using OpenAI's Agents framework.

## 🎯 Overview

AI Clinic uses a coordinated team of AI agents to evaluate patient symptoms and provide medical assessments through natural, empathetic conversations:

1. **Triage Nurse (Sarah Conner)** - Welcomes patients and collects initial complaints
2. **Resident Physician (Dr. Joan Crawford)** - Conducts follow-up questions and web research on symptoms
3. **Chief Physician (Dr. Stephen Hawking)** - Coordinates three specialists for comprehensive diagnosis:
   - **Emergency Specialist (Dr. Stephie Curran)** - Assesses urgency and emergency status
   - **Medicine Specialist (Dr. Kinsley Johnson)** - Evaluates need for medications and medical treatment
   - **Surgery Specialist (Dr. Rebeccah Meyers)** - Determines if surgical intervention is needed

## ✨ Key Features

• **Multi-Agent Architecture** - Coordinated team of 6 AI agents working together for comprehensive medical assessment

• **Consent-Based Workflow** - Patient approval required at every handoff stage, ensuring patient autonomy and comfort throughout the consultation process

• **Natural Conversational Flow** - One question at a time with empathetic responses, avoiding clinical questionnaires and numbered lists for a human-like interaction

• **Fully Dynamic AI Responses** - Zero hardcoded text; every introduction, question, and response is AI-generated in real-time for authentic, context-aware conversations

• **Parallel Specialist Consultation** - Chief Physician coordinates Emergency, Medicine, and Surgery specialists simultaneously, synthesizing their structured reports into actionable medical guidance

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- OpenAI API key (with access to the Agents API)

### Installation

1. **Install dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

2. **Set up environment variables:**

   Create a `.env` file in the AI_Clinic directory:

   ```bash
   OPENAI_API_KEY=your_api_key_here
   ```

   **Note:** The `WebSearchTool` is a hosted tool provided by OpenAI. No additional API keys required.

3. **Run the application:**

   ```bash
   python app.py
   ```

4. **Access the application:**

   Open your browser to `http://localhost:7860`

## 🏗️ Architecture

```
Patient Input
    ↓
Triage Nurse (Conversational)
    ↓ (collects complaint, asks consent)
Resident Physician (Conversational)
    ↓ (asks questions, researches, asks consent)
Chief Physician (Conversational)
    ↓ (introduces self, asks consent)
    ├─→ Emergency Specialist (Structured Output)
    ├─→ Medicine Specialist (Structured Output)
    └─→ Surgery Specialist (Structured Output)
    ↓ (synthesizes findings)
Final Comprehensive Report
```

## 📁 Project Structure

```
AI_Clinic/
├── app.py                              # Main Gradio chat application
├── config.py                           # Centralized agent names
├── triage_nurse_agent.py              # Triage Nurse (Sarah Conner)
├── resident_physician_agent.py        # Resident Physician (Joan Crawford)
├── chief_physician_agent.py           # Chief Physician (Dr. Stephen Hawking)
├── consultants/
│   ├── emergeny_specialist_agent.py   # Emergency assessment
│   ├── medicine_specialist_agent.py   # Medical treatment evaluation
│   └── surgery_specialist_agent.py    # Surgical assessment
├── requirements.txt
├── .gitignore
└── README.md
```

## 🔧 How It Works

### Stage 1: Triage Nurse (Sarah Conner)

- Greets the patient warmly and makes them comfortable
- Asks how they're feeling and what brings them in
- Collects initial complaint through natural conversation
- **Asks for patient consent** before handing off to Resident Physician
- Uses signal phrase `READY_FOR_RESIDENT_PHYSICIAN` to trigger handoff

### Stage 2: Resident Physician (Dr. Joan Crawford)

- Reviews triage conversation history
- Introduces themselves warmly
- Uses web search to research symptoms
- Asks up to 3 follow-up questions **ONE AT A TIME** in conversational manner
- Acknowledges responses and continues naturally (no numbered lists!)
- **Asks for patient consent** before handing off to Chief Physician
- Uses signal phrase `READY_FOR_CHIEF_PHYSICIAN` to trigger handoff

### Stage 3: Chief Physician (Dr. Stephen Hawking)

- Introduces themselves and reviews the case dynamically
- **Asks for patient consent** before consulting specialists
- Delegates to three specialist agents (as tools):
  - Emergency Specialist
  - Medicine Specialist
  - Surgery Specialist
- Waits for patient to confirm readiness before showing results
- Delivers comprehensive final assessment in structured format
- Consultation ends after results delivery

## 💡 Usage Example

### Natural Conversation Flow:

**Patient:** "Hi"  
**Triage Nurse:** "Hello! Welcome! How are you feeling today?"

**Patient:** "I've been having severe headaches"  
**Triage Nurse:** "I'm sorry to hear that. I'd like to connect you with our Resident Physician for a thorough evaluation. Would that be okay?"

**Patient:** "Yes, please"  
**Triage Nurse:** "Great! Please hold on while I connect you..."

**Resident Physician:** "Hello! I'm Dr. Crawford. I see you're experiencing headaches. Can you tell me how long you've been having them?"  
_[Uses web search to research]_

**Patient:** "About 3 days now"  
**Resident Physician:** "Thank you for sharing. On a scale of 1-10, how severe is the pain?"

**Patient:** "Around 7 or 8"  
**Resident Physician:** "I have a good understanding now. I'd like to consult with our Chief Physician and specialist team. Would you be comfortable with that?"

**Patient:** "Yes"  
**Resident Physician:** "Excellent! I'll bring in our Chief Physician..."

**Chief Physician:** "Hello! I'm Dr. Hawking. I'd like to consult with three specialists to give you the most comprehensive assessment. Would that be okay?"

**Patient:** "Sure"  
**Chief Physician:** "Excellent! Give me a moment..."  
_[Consults Emergency, Medicine, and Surgery Specialists]_  
**Chief Physician:** "Your results are ready! Let me know when you'd like to see them."

**Patient:** "I'm ready"
_[Delivers comprehensive medical assessment report]_

## ⚠️ Important Disclaimer

**This is an educational demonstration only.** This system is NOT:

- A substitute for professional medical advice
- Suitable for actual medical diagnosis
- Approved for clinical use
- Validated by medical professionals

**Always consult a qualified healthcare provider for medical concerns.**

## 🔍 Debugging

Each consultation generates a trace ID that can be viewed on the OpenAI platform:

```
https://platform.openai.com/traces/trace?trace_id={trace_id}
```

This allows you to see:

- All agent interactions
- Tool calls made (including specialist consultations)
- Decision-making process
- API usage and costs

## 🛠️ Customization

### Modify Agent Names

Edit `config.py` to change agent names:

```python
TRIAGE_NURSE_NAME = "Your Name"
RESIDENT_PHYSICIAN_NAME = "Dr. Your Name"
CHIEF_PHYSICIAN_NAME = "Dr. Your Name"
```

All agent instructions will automatically update!

### Modify Agent Behavior

Edit the `INSTRUCTIONS` variable in each agent file to change behavior.

### Change Models

Update the `model` parameter in agent initialization:

- `gpt-4o-mini` - Faster, cheaper (current default for most agents)
- `gpt-4o` - More capable (used for Chief Physician)

### Add More Specialists

1. Create new specialist agent in `consultants/`
2. Import in `chief_physician_agent.py`
3. Convert to tool using `.as_tool()`
4. Add to Chief Physician's tools list

## 📊 Agent Models Used

- **Triage Nurse (Sarah Conner)**: `gpt-4o-mini` - Conversational agent
- **Resident Physician (Dr. Joan Crawford)**: `gpt-4o-mini` (with WebSearchTool) - Conversational agent
- **Emergency Specialist (Dr. Stephie Curran)**: `gpt-4o-mini` (with WebSearchTool) - Structured output
- **Medicine Specialist (Dr. Kinsley Johnson)**: `gpt-4o-mini` (with WebSearchTool) - Structured output
- **Surgery Specialist (Dr. Rebeccah Meyers)**: `gpt-4o-mini` (with WebSearchTool) - Structured output
- **Chief Physician (Dr. Stephen Hawking)**: `gpt-4o` (orchestrator) - Dynamic conversational and structured output

## 🎨 Design Principles

### Consent-Based Workflow

- **Every handoff requires patient consent**
- Triage Nurse asks permission before connecting to Resident Physician
- Resident Physician asks permission before consulting Chief Physician
- Chief Physician asks permission before consulting specialists
- Chief Physician asks permission before showing results

### Natural Conversation

- Resident Physician asks ONE question at a time (no numbered lists)
- Empathetic and conversational responses
- Acknowledgment of patient responses before proceeding
- Dynamic AI-generated responses (zero hardcoded text)

### Role-Based Chat Display

- Each message shows who's speaking: 👤 Patient, 🩺 Triage Nurse, 🩺 Resident Physician, 🩺 Chief Physician, 🏥 AI Clinic
- Clean bubble interface with role labels above each message
- Dynamic status tracker showing current consultation stage

## 🚀 Deployment

### Deploy to Hugging Face Spaces

```bash
gradio deploy
```

Follow the prompts and add your `OPENAI_API_KEY` in the Space settings after deployment.

## 📝 Technical Details

### Signal Phrases

The system uses signal phrases to trigger handoffs:

- `READY_FOR_RESIDENT_PHYSICIAN` - Triage → Resident
- `READY_FOR_CHIEF_PHYSICIAN` - Resident → Chief
- `READY_FOR_SPECIALIST_CONSULTATION` - Chief → Specialists

### Conversation History

Each agent maintains its own conversation history and receives context from previous agents when taking over.

### Structured Outputs

Only specialist agents use Pydantic models with `ConfigDict(extra='forbid')` for strict JSON schema compliance. Primary care agents (Triage, Resident, Chief) are purely conversational.

## 📝 License

This is an educational project for learning purposes.

## 🤝 Contributing

This project is part of an AI agents learning curriculum. Feel free to fork and experiment!

## 👨‍💻 Author

Created as part of the Andela AI Agents training program.

---

**Built with ❤️ using OpenAI Agents SDK and Gradio**

