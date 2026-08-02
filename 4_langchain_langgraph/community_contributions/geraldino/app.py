import gradio as gr
from sidekick import Sidekick, login_user, init_user_db
import asyncio


# ─────────────────────────────────────────────
# Auth
# ─────────────────────────────────────────────

async def handle_login(username, password):
    """Authenticate or auto-register user. Returns their persistent sidekick_id."""
    if not username or not password:
        return None, None, gr.update(visible=True), gr.update(visible=False), "⚠️ Please enter a username and password."

    sidekick_id = await login_user(username, password)

    if sidekick_id is None:
        return None, None, gr.update(visible=True), gr.update(visible=False), "❌ Incorrect password."

    # Boot up their Sidekick with their persistent ID
    sidekick = Sidekick(sidekick_id=sidekick_id)
    await sidekick.setup()

    welcome = f"✅ Welcome back, **{username}**! Your previous conversations have been restored." \
        if sidekick_id else f"✅ Welcome, **{username}**! Your account has been created."

    return sidekick, sidekick_id, gr.update(visible=False), gr.update(visible=True), welcome


async def handle_logout(sidekick):
    free_resources(sidekick)
    return None, None, gr.update(visible=True), gr.update(visible=False), "", "", None, ""


# ─────────────────────────────────────────────
# Chat
# ─────────────────────────────────────────────

async def process_message(sidekick, message, success_criteria, history):
    if not sidekick:
        return history + [{"role": "assistant", "content": "⚠️ Please log in first."}], sidekick
    if not message.strip():
        return history, sidekick
    results = await sidekick.run_superstep(message, success_criteria, history)
    return results, sidekick


async def reset_chat(sidekick):
    """Clear the chat display but keep the same user session and SQL memory."""
    return "", "", None


def free_resources(sidekick):
    print("Cleaning up sidekick resources")
    try:
        if sidekick:
            sidekick.cleanup()
    except Exception as e:
        print(f"Exception during cleanup: {e}")


# ─────────────────────────────────────────────
# UI
# ─────────────────────────────────────────────

with gr.Blocks(title="Sidekick", theme=gr.themes.Default(primary_hue="emerald")) as ui:

    # Shared state
    sidekick_state = gr.State(delete_callback=free_resources)
    sidekick_id_state = gr.State()

    async def initialize():
        await init_user_db()

    # ── Login panel ───────────────────────────
    with gr.Column(visible=True) as login_panel:
        gr.Markdown("## 🤖 Sidekick — Personal Co-Worker")
        gr.Markdown("Login to continue your work, or create a new account by entering a new username.")

        login_status = gr.Markdown("")
        username_input = gr.Textbox(label="Username", placeholder="e.g. john_doe")
        password_input = gr.Textbox(label="Password", type="password", placeholder="Your password")
        login_button = gr.Button("Login / Register", variant="primary")

    # ── Main app panel ────────────────────────
    with gr.Column(visible=False) as main_panel:
        gr.Markdown("## 🤖 Sidekick — Personal Co-Worker")
        auth_status = gr.Markdown("")

        with gr.Row():
            chatbot = gr.Chatbot(label="Sidekick", height=400, type="messages")

        with gr.Group():
            with gr.Row():
                message = gr.Textbox(
                    show_label=False,
                    placeholder="Your request to the Sidekick",
                    scale=4
                )
            with gr.Row():
                success_criteria = gr.Textbox(
                    show_label=False,
                    placeholder="Success criteria (optional — e.g. 'give me a bullet point summary')"
                )

        with gr.Row():
            logout_button = gr.Button("Logout", variant="stop")
            reset_button = gr.Button("Clear Chat", variant="secondary")
            go_button = gr.Button("Go!", variant="primary")

        gr.Markdown(
            "_The Sidekick may ask up to 3 clarifying questions before starting work. "
            "Your chat history is saved and restored on next login._",
            elem_id="footer"
        )

    # ── Event wiring ──────────────────────────

    # Init user DB on load
    # ui.load(lambda: asyncio.get_event_loop().run_until_complete(init_user_db()), [], [])
    ui.load(init_user_db, [], [])

    login_button.click(
        handle_login,
        [username_input, password_input],
        [sidekick_state, sidekick_id_state, login_panel, main_panel, login_status]
    )
    password_input.submit(
        handle_login,
        [username_input, password_input],
        [sidekick_state, sidekick_id_state, login_panel, main_panel, login_status]
    )

    go_button.click(
        process_message,
        [sidekick_state, message, success_criteria, chatbot],
        [chatbot, sidekick_state]
    )
    message.submit(
        process_message,
        [sidekick_state, message, success_criteria, chatbot],
        [chatbot, sidekick_state]
    )

    reset_button.click(
        reset_chat,
        [sidekick_state],
        [message, success_criteria, chatbot]
    )

    logout_button.click(
        handle_logout,
        [sidekick_state],
        [sidekick_state, sidekick_id_state, login_panel, main_panel, message, success_criteria, chatbot, auth_status]
    )


ui.launch(inbrowser=True)
