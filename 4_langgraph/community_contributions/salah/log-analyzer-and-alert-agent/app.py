import gradio as gr
from config import LogAnalyzerConfig
from log_analyzer_agent import LogAnalyzerAgent
import os


async def setup():
    config = LogAnalyzerConfig()
    agent = LogAnalyzerAgent(config)
    await agent.setup()
    return agent, config


async def analyze(agent, log_file, criteria, history):
    if not log_file:
        error_msg = {"role": "assistant", "content": "Please select a log file to analyze."}
        return history + [error_msg], agent

    log_file_path = os.path.join(agent.config.logs_directory, log_file)

    results = await agent.analyze_log(log_file_path, criteria, history)
    return results, agent


async def reset():
    new_agent, new_config = await setup()
    return "", "", None, new_agent, new_config


def cleanup_agent(agent):
    if agent:
        try:
            agent.cleanup()
        except Exception:
            pass


def update_config(
    agent,
    config,
    logs_dir,
    source_dir,
    error_patterns,
    max_errors,
    enable_source,
    enable_notif,
    enable_browser
):
    if config:
        config.logs_directory = logs_dir
        config.source_code_directory = source_dir
        config.error_patterns = [p.strip() for p in error_patterns.split(",")]
        config.max_errors_to_analyze = max_errors
        config.enable_source_investigation = enable_source
        config.enable_notifications = enable_notif
        config.enable_browser_tools = enable_browser

        validation = config.validate_directories()
        status_msg = "Configuration updated successfully\n\n"

        if not validation["logs_directory_exists"]:
            status_msg += f"Warning: Logs directory '{logs_dir}' does not exist\n"
        if not validation["source_code_directory_exists"]:
            status_msg += f"Warning: Source code directory '{source_dir}' does not exist\n"

        log_files = agent.get_log_files() if agent else []

        return status_msg, gr.update(choices=log_files, value=log_files[0] if log_files else None)

    return "Agent not initialized", gr.update()


def refresh_log_files(agent):
    if agent:
        log_files = agent.get_log_files()
        return gr.update(choices=log_files, value=log_files[0] if log_files else None)
    return gr.update()


with gr.Blocks(title="Log Analyzer & Alert Agent", theme=gr.themes.Default(primary_hue="blue")) as ui:
    gr.Markdown("# Log Analyzer & Alert Agent")
    gr.Markdown("*AI-powered DevOps log analysis with source code investigation and intelligent alerting*")

    agent_state = gr.State(delete_callback=cleanup_agent)
    config_state = gr.State()

    with gr.Accordion("Configuration", open=False):
        with gr.Row():
            logs_dir_input = gr.Textbox(
                label="Logs Directory",
                value="logs",
                placeholder="logs"
            )
            source_dir_input = gr.Textbox(
                label="Source Code Directory",
                value="source_code",
                placeholder="source_code"
            )

        with gr.Row():
            error_patterns_input = gr.Textbox(
                label="Error Patterns (comma-separated)",
                value="ERROR, FATAL, Exception, Traceback",
                placeholder="ERROR, FATAL, Exception"
            )
            max_errors_input = gr.Slider(
                label="Max Errors to Analyze",
                minimum=1,
                maximum=20,
                value=5,
                step=1
            )

        with gr.Row():
            enable_source_input = gr.Checkbox(
                label="Enable Source Code Investigation",
                value=True
            )
            enable_notif_input = gr.Checkbox(
                label="Enable Push Notifications",
                value=True
            )
            enable_browser_input = gr.Checkbox(
                label="Enable Browser Tools (requires 'playwright install chromium')",
                value=False
            )

        with gr.Row():
            update_config_btn = gr.Button("Update Configuration", variant="secondary")
            config_status = gr.Textbox(
                label="Configuration Status",
                interactive=False,
                lines=3
            )

    gr.Markdown("---")

    with gr.Row():
        with gr.Column(scale=2):
            log_file_dropdown = gr.Dropdown(
                label="Select Log File",
                choices=[],
                interactive=True
            )
        with gr.Column(scale=1):
            refresh_btn = gr.Button("Refresh Files", size="sm")

    criteria_input = gr.Textbox(
        label="Analysis Criteria",
        placeholder="Examples:\n• Find all FATAL and ERROR messages and prioritize by severity\n• Investigate NullPointerException errors in the source code and suggest fixes\n• Analyze database connection failures and search for solutions online\n• Find all errors, categorize them, and send notification for critical ones\n\nLeave empty for default: 'Find and analyze all errors in the log file'",
        lines=5
    )

    with gr.Row():
        analyze_btn = gr.Button("Analyze", variant="primary", size="lg")
        reset_btn = gr.Button("Reset", variant="stop")

    gr.Markdown("---")

    chatbot = gr.Chatbot(
        label="Analysis Results",
        height=500,
        type="messages",
        show_label=True
    )

    gr.Markdown("---")
    gr.Markdown("""
    ### Usage Tips:
    - **Simple**: Select a log file and click Analyze
    - **Custom**: Specify criteria like "Find all database connection errors"
    - **Source Investigation**: Automatically investigates referenced code files
    - **Notifications**: Get alerts for FATAL errors (requires Pushover setup)

    ### Example Queries:
    - "Find all ERROR and FATAL messages and categorize by severity"
    - "Investigate NullPointerException errors and suggest fixes"
    - "Analyze connection timeout errors and search for solutions online"
    """)

    ui.load(
        setup,
        [],
        [agent_state, config_state]
    ).then(
        refresh_log_files,
        [agent_state],
        [log_file_dropdown]
    )

    analyze_btn.click(
        analyze,
        [agent_state, log_file_dropdown, criteria_input, chatbot],
        [chatbot, agent_state]
    )

    criteria_input.submit(
        analyze,
        [agent_state, log_file_dropdown, criteria_input, chatbot],
        [chatbot, agent_state]
    )

    reset_btn.click(
        reset,
        [],
        [criteria_input, chatbot, log_file_dropdown, agent_state, config_state]
    ).then(
        refresh_log_files,
        [agent_state],
        [log_file_dropdown]
    )

    update_config_btn.click(
        update_config,
        [
            agent_state,
            config_state,
            logs_dir_input,
            source_dir_input,
            error_patterns_input,
            max_errors_input,
            enable_source_input,
            enable_notif_input,
            enable_browser_input
        ],
        [config_status, log_file_dropdown]
    )

    refresh_btn.click(
        refresh_log_files,
        [agent_state],
        [log_file_dropdown]
    )


ui.launch(inbrowser=True)
