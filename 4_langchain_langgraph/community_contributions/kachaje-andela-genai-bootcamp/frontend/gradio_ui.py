import gradio as gr
import requests
from typing import Tuple, Optional
from backend.utils.logger import get_logger

logger = get_logger()


API_BASE = "http://localhost:8000"
session_id: Optional[str] = None
current_state = "challenge"
plan_text = ""
build_messages = []


def get_state_label(state: str) -> str:
    labels = {
        "challenge": "Submit Challenge",
        "plan": "Build Project",
        "build": "Done",
        "busy": "Please Wait...",
    }
    return labels.get(state, "Submit")


def get_input_placeholder(state: str) -> str:
    placeholders = {
        "challenge": "Enter your challenge here (e.g., Create a calculator app, Build a REST API, etc.)",
        "plan": "Review the plan above and click 'Build Project' when ready",
        "build": "Project build complete! Click 'Done' to start a new project",
        "busy": "Please wait while we process your request...",
    }
    return placeholders.get(state, "Enter your input here...")


def run_action(input_text: str, output_text: str) -> Tuple[str, str, gr.Button]:
    global session_id, current_state, plan_text, build_messages

    logger.logger.info(
        f"UI action triggered: state={current_state}, input_length={len(input_text)}"
    )

    if not session_id:
        try:
            logger.logger.info("Creating new session from UI")
            response = requests.post(f"{API_BASE}/api/session")
            session_id = response.json()["session_id"]
            current_state = "challenge"
            plan_text = ""
            build_messages = []
            logger.log_session_event("created", session_id, {"source": "gradio_ui"})
        except Exception as e:
            logger.logger.error(
                f"Error creating session from UI: {str(e)}", exc_info=True
            )
            error_msg = f"Error creating session: {str(e)}"
            return (
                input_text,
                error_msg,
                gr.Button(value=get_state_label(current_state), interactive=True),
            )

    if current_state == "busy":
        logger.logger.debug(f"UI action ignored: session {session_id} is busy")
        return (
            input_text,
            output_text,
            gr.Button(value="Please Wait...", interactive=False),
        )

    try:
        if current_state == "challenge":
            logger.logger.info(
                f"Submitting challenge from UI: session={session_id}, challenge_length={len(input_text)}"
            )
            
            plan_text = ""  # Reset plan text for new challenge
            
            response = requests.post(
                f"{API_BASE}/api/session/{session_id}/challenge",
                json={"challenge": input_text},
            )
            result = response.json()
            old_state = current_state
            current_state = result["state"]
            logger.logger.info(
                f"Challenge submitted: session={session_id}, state transition: {old_state} -> {current_state}"
            )
            
            # Show the plan from the response
            if result.get("plan"):
                plan_text = result.get("plan", "")
                output = f"## Plan\n\n{plan_text}"
            else:
                output = "## Generating Plan...\n\nPlease wait..."
            
            is_busy = current_state == "busy"
            return (
                "",
                output,
                gr.Button(
                    value=get_state_label(current_state), interactive=not is_busy
                ),
            )

        elif current_state == "plan":
            logger.logger.info(f"Triggering build from UI: session={session_id}")
            old_state = current_state
            current_state = "busy"
            build_messages = []  # Reset build messages
            
            logger.log_state_transition(
                session_id=session_id,
                from_state=old_state,
                to_state=current_state,
                context={"source": "gradio_ui", "action": "build"},
            )
            response = requests.post(f"{API_BASE}/api/session/{session_id}/build")
            result = response.json()
            
            # Show the result from the response
            if result.get("status") != "building" and result.get("files_created"):
                current_state = "build"
                files = "\n".join([f"- {f}" for f in result.get("files_created", [])])
                output = f"## Project Built!\n\n### Files Created:\n{files}\n\n### Project Path:\n{result.get('project_path', '')}"
                logger.logger.info(
                    f"Build completed: session={session_id}, files_count={len(result.get('files_created', []))}"
                )
            else:
                output = "## Building Project...\n\nPlease wait..."
            
            return (
                input_text,
                output,
                gr.Button(value=get_state_label(current_state), interactive=True),
            )

        elif current_state == "build":
            logger.logger.info(f"Resetting session from UI: session={session_id}")
            old_session_id = session_id
            session_id = None
            current_state = "challenge"
            plan_text = ""
            build_messages = []
            logger.log_session_event("reset", old_session_id, {"source": "gradio_ui"})
            return (
                "",
                "",
                gr.Button(value=get_state_label(current_state), interactive=True),
            )

    except Exception as e:
        logger.logger.error(
            f"Error in UI action: session={session_id}, state={current_state}, error={str(e)}",
            exc_info=True,
        )
        return (
            input_text,
            f"Error: {str(e)}",
            gr.Button(value=get_state_label(current_state), interactive=True),
        )

    return (
        input_text,
        output_text,
        gr.Button(value=get_state_label(current_state), interactive=True),
    )


def clear_session() -> Tuple[str, str, gr.Button]:
    global session_id, current_state, plan_text, build_messages

    if session_id:
        logger.logger.info(f"Clearing session from UI: session={session_id}")
        try:
            requests.delete(f"{API_BASE}/api/session/{session_id}")
            logger.log_session_event(
                "cleared", session_id, {"source": "gradio_ui", "action": "clear_button"}
            )
        except Exception as e:
            logger.logger.warning(f"Error clearing session from UI: {str(e)}")

    old_session_id = session_id
    session_id = None
    current_state = "challenge"
    plan_text = ""
    build_messages = []
    logger.logger.info(
        f"Session cleared: old_session={old_session_id}, new_state={current_state}"
    )
    return (
        "",
        "",
        gr.Button(value=get_state_label(current_state), interactive=True),
    )


with gr.Blocks() as demo:
    gr.Markdown("# CodeBuilder")

    with gr.Row():
        output_box = gr.Markdown(label="Output")

    with gr.Row():
        input_box = gr.Textbox(
            label="Input",
            lines=10,
            placeholder="Enter your challenge here...",
            interactive=True,
        )

    with gr.Row():
        clear_btn = gr.Button("Clear", variant="secondary")
        run_btn = gr.Button("Submit Challenge", variant="primary")

    run_btn.click(
        fn=run_action,
        inputs=[input_box, output_box],
        outputs=[input_box, output_box, run_btn],
    )

    clear_btn.click(fn=clear_session, outputs=[input_box, output_box, run_btn])

if __name__ == "__main__":
    logger.logger.info("Starting Gradio UI on 0.0.0.0:7860")
    demo.launch(server_name="0.0.0.0", server_port=7860)
