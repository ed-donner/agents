import gradio as gr
import sys
import logging
import queue
import threading
from pathlib import Path
from typing import Optional
try:
    from .sidekick import Sidekick, FIXED_WORKSPACE
except ImportError:
    current_file = Path(__file__).resolve()
    langgraph_dir = current_file.parent.parent.parent.parent
    if str(langgraph_dir) not in sys.path:
        sys.path.insert(0, str(langgraph_dir))
    from community_contributions.iamumarjaved.sidekick_agent.sidekick import Sidekick, FIXED_WORKSPACE
FIXED_WORKSPACE_PATH = str(FIXED_WORKSPACE.resolve())
try:
    from .shared_state import update_validator_output as _update_validator, get_validator_output, get_plan_output
except ImportError:
    from community_contributions.iamumarjaved.sidekick_agent.shared_state import update_validator_output as _update_validator, get_validator_output, get_plan_output
log_queue = queue.Queue()
log_buffer = []


class GradioLogHandler(logging.Handler):
    """Custom logging handler that streams logs to Gradio UI."""
    
    def emit(self, record):
        try:
            log_entry = self.format(record)
            log_queue.put(log_entry)
            log_buffer.append(log_entry)
            if len(log_buffer) > 1000:
                log_buffer.pop(0)
        except Exception:
            pass


def get_logs():
    """Get all logs from the queue and return as string."""
    logs = []
    try:
        while True:
            logs.append(log_queue.get_nowait())
    except queue.Empty:
        pass
    
    if logs:
        log_buffer.extend(logs)
        if len(log_buffer) > 1000:
            log_buffer[:] = log_buffer[-1000:]
    
    return "\n".join(log_buffer[-500:])


def stream_logs():
    """Generator that yields log updates in real-time."""
    import time
    last_count = len(log_buffer)
    while True:
        logs = []
        try:
            while True:
                logs.append(log_queue.get_nowait())
        except queue.Empty:
            pass
        
        if logs:
            log_buffer.extend(logs)
            if len(log_buffer) > 1000:
                log_buffer[:] = log_buffer[-1000:]
            yield "\n".join(log_buffer[-500:])
        elif len(log_buffer) != last_count:
            yield "\n".join(log_buffer[-500:])
            last_count = len(log_buffer)
        else:
            yield "\n".join(log_buffer[-500:])
        
        time.sleep(0.5)


def update_ui_periodically():
    """Periodically update UI components with latest logs and validator output."""
    import time
    while True:
        time.sleep(0.5)
        yield {
            "logs": get_logs(),
            "validator": get_validator_output()
        }


class StreamToLogger:
    """Redirect stdout/stderr to logging so all print statements are captured."""
    def __init__(self, logger, log_level=logging.INFO, original_stream=None):
        self.logger = logger
        self.log_level = log_level
        self.original_stream = original_stream
        self.linebuf = ''

    def write(self, buf):

        temp_linebuf = self.linebuf + buf
        self.linebuf = ''
        for line in temp_linebuf.splitlines(True):
            if line[-1] == '\n':
                self.logger.log(self.log_level, line.rstrip())
            else:
                self.linebuf = line

    def flush(self):
        if self.linebuf:
            self.logger.log(self.log_level, self.linebuf.rstrip())
            self.linebuf = ''


def setup_logging():
    """Setup logging to stream to Gradio."""
    original_stdout = sys.stdout
    original_stderr = sys.stderr
    
    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    gradio_handler = GradioLogHandler()
    gradio_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    root_logger.addHandler(gradio_handler)
    root_logger.setLevel(logging.INFO)
    
    console_handler = logging.StreamHandler(original_stdout)
    console_handler.setFormatter(logging.Formatter('%(message)s'))
    root_logger.addHandler(console_handler)
    
    sys.stdout = StreamToLogger(root_logger, logging.INFO, original_stream=original_stdout)
    sys.stderr = StreamToLogger(root_logger, logging.ERROR, original_stream=original_stderr)


async def setup():
    try:
        setup_logging()
        
        print("="*80)
        print(f"FIXED WORKSPACE PATH: {FIXED_WORKSPACE_PATH}")
        print("   All task files will be created in this directory")
        print("="*80)
        print("Initializing Sidekick...")
        sidekick = Sidekick()
        print("Sidekick instance created, setting up...")
        await sidekick.setup()
        print("Sidekick setup completed successfully!")
        return sidekick
    except Exception as e:
        import traceback
        error_traceback = traceback.format_exc()
        error_msg = f"Setup failed: {str(e)}\n\nPlease ensure:\n- Playwright browsers are installed: run 'playwright install'\n- All dependencies are installed (chromadb, sentence-transformers)\n- OpenAI API key is set (if using OpenAI embeddings)\n\nFull error:\n{error_traceback}"
        print(f"ERROR: {error_msg}")
        return None


async def process_message(sidekick, chatbot_history, message):
    """Process the user message and update chatbot history."""
    if sidekick is None:
        error_msg = "Sidekick not initialized. Please check the console for setup errors."
        return (
            chatbot_history + [{"role": "user", "content": message}, {"role": "assistant", "content": error_msg}],
            "",
            sidekick,
            "", "", error_msg, "", "", "", "", "", "", ""
        )

    if not message or not message.strip():
        return chatbot_history, "", sidekick, "", "", "", "", "", "", "", "", "", ""

    prompt = message.strip()

    try:
        from .shared_state import clear_validator_output, clear_plan_output, clear_status
        clear_validator_output()
        clear_plan_output()
        clear_status()
    except ImportError:
        try:
            from community_contributions.iamumarjaved.sidekick_agent.shared_state import clear_validator_output, clear_plan_output, clear_status
            clear_validator_output()
            clear_plan_output()
            clear_status()
        except ImportError:
            pass

    global last_file_mtimes
    last_file_mtimes.clear()
    
    updated_history = chatbot_history + [{"role": "user", "content": prompt}]

    try:
        results = await sidekick.run_superstep(prompt)
    except Exception as e:
        error_msg = f"Error processing prompt: {str(e)}"
        logs = get_logs()
        return (
            updated_history + [{"role": "assistant", "content": error_msg}],
            "",
            sidekick,
            "", "", error_msg, "", "", "", logs
        )
    artifacts = results.get("artifacts", {})
    
    validation_report = results.get("validation_report", "")
    if validation_report:
        _update_validator(validation_report)
    
    assistant_response = f"Task completed!\n\nPlan: {results.get('plan', 'N/A')[:200]}...\n\nValidation: {results.get('validation_report', 'N/A')[:200]}...\n\nReview: {results.get('review_summary', 'N/A')[:200]}..."
    updated_history = updated_history + [{"role": "assistant", "content": assistant_response}]
    
    logs = get_logs()

    return (
        updated_history,
        "",
        sidekick,
        results.get("plan", ""),
        results.get("validation_report", ""),
        results.get("review_summary", ""),
        artifacts.get("main.py", ""),
        artifacts.get("test.py", ""),
        FIXED_WORKSPACE_PATH,
        logs,
    )


def save_file(sidekick, workspace, filename, content):
    """Save file content back to the fixed workspace."""
    if sidekick is None:
        gr.Warning(f"Cannot save {filename} - sidekick not available")
        return

    try:
        workspace_path = Path(FIXED_WORKSPACE_PATH)
        workspace_path.mkdir(parents=True, exist_ok=True)

        file_path = workspace_path / filename

        file_path.write_text(content, encoding="utf-8")
        gr.Info(f"{filename} saved successfully!")
    except Exception as e:
        gr.Warning(f"Error saving {filename}: {str(e)}")


def reload_files(workspace=None):
    """Reload all files from the fixed workspace directory."""
    try:
        workspace_path = Path(FIXED_WORKSPACE_PATH)
        workspace_path.mkdir(parents=True, exist_ok=True)
        if not workspace_path.exists():
            return "", ""

        files = {
            "main.py": "",
            "test.py": "",
        }

        for filename in files.keys():
            file_path = workspace_path / filename
            if file_path.exists():
                try:
                    files[filename] = file_path.read_text(encoding="utf-8")
                except Exception as e:
                    files[filename] = f"# Error reading file: {e}"

        return (
            files["main.py"],
            files["test.py"],
        )
    except Exception as e:
        return "", ""


last_file_mtimes = {}

def auto_reload_files():
    """Auto-reload files if they've been modified. Called by timer."""
    global last_file_mtimes
    no_update = (gr.skip(), gr.skip())

    try:
        workspace_path = Path(FIXED_WORKSPACE_PATH)
        if not workspace_path.exists():
            return no_update

        files_changed = False
        for filename in ["main.py", "test.py"]:
            file_path = workspace_path / filename
            if file_path.exists():
                try:
                    current_mtime = file_path.stat().st_mtime
                    if filename not in last_file_mtimes or last_file_mtimes[filename] != current_mtime:
                        last_file_mtimes[filename] = current_mtime
                        files_changed = True
                except Exception:
                    pass

        if files_changed:
            return reload_files()
        else:
            return no_update
    except Exception:
        return no_update


async def reset():
    try:
        new_sidekick = Sidekick()
        await new_sidekick.setup()
        return [], "", "", "", "", "", "", "", new_sidekick
    except Exception as e:
        error_msg = f"Reset failed: {str(e)}"
        print(f"ERROR: {error_msg}")
        return [], "", "", "", error_msg, "", "", "", None


def free_resources(sidekick):
    try:
        if sidekick:
            sidekick.cleanup()
    except Exception as exc:
        print(f"Cleanup warning: {exc}")


def build_ui() -> gr.Blocks:
    with gr.Blocks(title="IAMUmar Sidekick", theme=gr.themes.Default(primary_hue="emerald")) as ui:
        gr.Markdown("# 🤖 IAMUmar Code & Test Generator")
        sidekick = gr.State(delete_callback=free_resources)
        workspace_path = gr.State("")

        with gr.Row():
            status_display = gr.Textbox(
                label="Status",
                value="Idle",
                interactive=False,
                max_lines=1,
                scale=3,
            )
            iteration_display = gr.Textbox(
                label="Iteration",
                value="0",
                interactive=False,
                max_lines=1,
                scale=1,
            )

        with gr.Accordion("📈 Progress Timeline", open=False):
            progress_log = gr.Textbox(
                lines=8,
                interactive=False,
                value="⏳ Waiting to start...",
                show_copy_button=True,
                show_label=False,
            )

        chatbot = gr.Chatbot(
            label="Chat with Sidekick",
            height=400,
            type="messages",
        )
        
        msg = gr.Textbox(
            label="Type your message",
            placeholder="Enter your task prompt or ask questions about the code...",
            lines=3,
        )

        with gr.Row():
            submit_btn = gr.Button("Send", variant="primary", scale=4)
            reset_button = gr.Button("Reset Session", variant="stop", scale=1)

        with gr.Accordion("Execution Reports", open=True):
            with gr.Row():
                plan_box = gr.Textbox(label="Plan", lines=8, interactive=False)
                validation_box = gr.Textbox(label="Validation", lines=8, interactive=False)
            review_box = gr.Textbox(label="Review", lines=5, interactive=False)
        
        with gr.Row():
            workspace_box = gr.Textbox(label="Workspace", interactive=False, scale=4)
            reload_files_btn = gr.Button("Reload", size="sm", scale=1)

        with gr.Tabs():
            with gr.Tab("Live Logs"):
                log_viewer = gr.Textbox(
                    label="Real-time execution logs (auto-refresh every 1s)",
                    lines=25,
                    interactive=False,
                    value="",
                    show_copy_button=True,
                )
                log_refresh_btn = gr.Button("Refresh Now", size="sm")

            with gr.Tab("Solution"):
                main_view = gr.Code(label="main.py", language="python", interactive=True)
                main_save = gr.Button("Save Changes", size="sm", variant="primary")

            with gr.Tab("Unit Tests"):
                test_view = gr.Code(label="test.py", language="python", interactive=True)
                test_save = gr.Button("Save Changes", size="sm", variant="primary")

        ui.load(setup, [], [sidekick])
        
        def set_fixed_workspace():
            return FIXED_WORKSPACE_PATH
        ui.load(set_fixed_workspace, [], [workspace_box])
        
        def update_logs_plan_and_validator():
            """Update logs, plan, and validator output."""
            return get_logs(), get_plan_output(), get_validator_output()

        def update_status_display():
            """Update status, iteration, and progress log."""
            try:
                from .shared_state import get_status
            except ImportError:
                try:
                    from community_contributions.iamumarjaved.sidekick_agent.shared_state import get_status
                except ImportError:
                    return "Idle", "0", "⏳ Status not available"

            status_info = get_status()
            return (
                status_info["status"],
                str(status_info["iteration"]),
                status_info["progress_log"]
            )
        
        def reload_files_with_logs(ws):
            """Reload files and update logs/validator."""
            files = reload_files(ws)
            logs = get_logs()
            validator = get_validator_output()
            return (*files, logs, validator)
        
        reload_files_btn.click(
            reload_files_with_logs,
            [workspace_box],
            [main_view, test_view, log_viewer, validation_box]
        )
        
        log_refresh_btn.click(
            update_logs_plan_and_validator,
            [],
            [log_viewer, plan_box, validation_box]
        )

        ui.load(
            update_logs_plan_and_validator,
            None,
            [log_viewer, plan_box, validation_box]
        )

        log_viewer_timer = gr.Timer(1.0)
        log_viewer_timer.tick(
            get_logs,
            None,
            [log_viewer]
        )

        file_viewer_timer = gr.Timer(2.0)
        file_viewer_timer.tick(
            auto_reload_files,
            None,
            [main_view, test_view]
        )

        status_timer = gr.Timer(0.5)
        status_timer.tick(
            update_status_display,
            None,
            [status_display, iteration_display, progress_log]
        )

        plan_validation_timer = gr.Timer(1.0)
        plan_validation_timer.tick(
            lambda: (get_plan_output(), get_validator_output()),
            None,
            [plan_box, validation_box]
        )
        
        
        submit_btn.click(
            process_message,
            [sidekick, chatbot, msg],
            [
                chatbot,
                msg,
                sidekick,
                plan_box,
                validation_box,
                review_box,
                main_view,
                test_view,
                workspace_box,
                log_viewer,
            ],
        ).then(
            lambda ws: ws,
            [workspace_box],
            [workspace_path]
        )

        msg.submit(
            process_message,
            [sidekick, chatbot, msg],
            [
                chatbot,
                msg,
                sidekick,
                plan_box,
                validation_box,
                review_box,
                main_view,
                test_view,
                workspace_box,
                log_viewer,
            ],
        ).then(
            lambda ws: ws,
            [workspace_box],
            [workspace_path]
        )
        def save_main(sk, ws, content):
            save_file(sk, ws, "main.py", content)
        def save_test(sk, ws, content):
            save_file(sk, ws, "test.py", content)

        main_save.click(
            save_main,
            [sidekick, workspace_path, main_view],
            None
        )
        test_save.click(
            save_test,
            [sidekick, workspace_path, test_view],
            None
        )

        reset_button.click(
            reset,
            [],
            [
                chatbot,
                msg,
                plan_box,
                validation_box,
                review_box,
                main_view,
                test_view,
                workspace_box,
                sidekick,
            ],
        ).then(
            lambda: "",
            [],
            [workspace_path]
        )

    return ui


def launch(inbrowser: bool = True):
    app = build_ui()
    app.launch(inbrowser=inbrowser)


if __name__ == "__main__":
    launch()

