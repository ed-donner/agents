# Week 9: Human-in-the-Loop

## What you'll build
A production-grade HITL framework: agents that pause at configurable checkpoints, surface their reasoning, request human approval (via CLI, Gradio, or email), incorporate feedback, and escalate when confidence is low.

## Learning objectives
- Insert approval gates that halt an agent mid-execution
- Implement confidence-based escalation: low confidence → human review
- Build a feedback loop so agents improve from corrections within a session
- Handle timeout/non-response gracefully (approve, reject, or escalate)
- Design multi-agent conflict resolution through human arbitration

## Labs

| Lab | Topic | Key pattern |
|-----|-------|-------------|
| `1_lab1.ipynb` | Approval gates | Agent pauses, human approves/rejects each step |
| `2_lab2.ipynb` | Confidence escalation | Structured confidence score → auto or human decision |
| `3_lab3.ipynb` | Feedback loops | Human corrects agent; agent applies correction to remaining steps |
| `4_lab4.ipynb` | Multi-agent arbitration | Two agents disagree; human resolves; both update |

## App
`app.py` — Gradio UI where you watch an agent plan a task step-by-step and approve/reject each action in real time.

## Cost estimate
~$0.02–0.10 per workflow run (most cost is the approval decision, not the agent itself).
