import asyncio
import logging

from quart import Quart, request
from telegram import Update, Bot
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters
from dotenv import load_dotenv
from google.adk.agents import Agent
from google.adk.runners import Runner

from google.genai import types

from modules.config import Config
from modules.setup_logging import setup_logging
from modules.tools.setup_sheets import initialize_google_sheets
from modules.agents.sequential_agents import create_agents
from modules.in_memory_session import InMemorySessionService
from modules.agents.order_status_agent import create_order_status_agent
from modules.agents.root_agent import create_root_agent

logger = setup_logging()

# --- Singleton Session Service ---
class SessionServiceSingleton:
    _instance = None

    @classmethod
    def get_instance(cls) -> InMemorySessionService:
        if cls._instance is None:
            cls._instance = InMemorySessionService()
        return cls._instance


# --- Session and Runner Setup ---
def setup_session_and_runner(config: Config, agent: Agent) -> tuple[InMemorySessionService, Runner]:
    session_service = SessionServiceSingleton.get_instance()
    runner = Runner(
        agent=agent,
        app_name=config.APP_NAME,
        session_service=session_service
    )
    return session_service, runner

# --- Agent Call ---
async def call_agent_async(
    user_id: str,
    session_id: str,
    query: str,
    runner: Runner,
    session_service: InMemorySessionService,
    logger: logging.Logger
) -> str:
    logger.info(f"Calling agent for user '{user_id}' with query: '{query}' in session '{session_id}'")
    session_key = f"{runner.app_name}:{user_id}:{session_id}"

    try:
        session = await session_service.get_session(app_name=runner.app_name, user_id=user_id, session_id=session_id, raise_error=False)
        if not session:
            session = await session_service.create_session(app_name=runner.app_name, user_id=user_id, session_id=session_id)
        logger.debug(f"Session ensured: {session_key}")
    except Exception as e:
        logger.error(f"Session creation failed: {e}")
        return "Error: Unable to initialize session."

    session_service.append_history(
        app_name=runner.app_name,
        user_id=user_id,
        session_id=session_id,
        role="user",
        text=query
    )

    session = await session_service.get_session(app_name=runner.app_name, user_id=user_id, session_id=session_id)
    custom_data = await session_service.get_custom_data(app_name=runner.app_name, user_id=user_id, session_id=session_id)
    if not custom_data:
        logger.error(f"Custom data not found for session {session_key}")
        return "Error: Session data unavailable."

    active_agent = custom_data.get("state", {}).get("active_agent", None)

    history = custom_data.get("history", [])
    content_parts = []
    for msg in history[-6:]:
        content_parts.append(types.Part(text=f"{msg['role']}: {msg['text']}"))
    content_parts.append(types.Part(text=f"user: {query}"))
    content = types.Content(role="user", parts=content_parts)

    final_response_text = "No response from agent."
    max_retries = 2

    for attempt in range(max_retries):
        try:
            def run_generator():
                nonlocal final_response_text
                events = runner.run(
                    user_id=user_id,
                    session_id=session_id,
                    new_message=content
                )

                for event in events:
                    if event.is_final_response():
                        if event.content and event.content.parts:
                            final_response_text = event.content.parts[0].text
                            # Handle order form agent state
                            if "Please provide the following details" in final_response_text or "Please confirm by replying 'confirm'" in final_response_text:
                                session_service.update_session(
                                    app_name=runner.app_name,
                                    user_id=user_id,
                                    session_id=session_id,
                                    data={"state": {
                                        "active_agent": "order_form_agent_v1",
                                        "order_details": custom_data.get("state", {}).get("order_details", {}),
                                        "bill_confirmed": custom_data.get("state", {}).get("bill_confirmed", False),
                                        "order_status_details": custom_data.get("state", {}).get("order_status_details", {})
                                    }}
                                )
                            # Handle order status agent state
                            elif "To check your order status" in final_response_text or "Please provide your phone number" in final_response_text or "Invalid Order ID format" in final_response_text:
                                session_service.update_session(
                                    app_name=runner.app_name,
                                    user_id=user_id,
                                    session_id=session_id,
                                    data={"state": {
                                        "active_agent": "order_status_agent_v1",
                                        "order_details": custom_data.get("state", {}).get("order_details", {}),
                                        "bill_confirmed": custom_data.get("state", {}).get("bill_confirmed", False),
                                        "order_status_details": custom_data.get("state", {}).get("order_status_details", {})
                                    }}
                                )
                            # Clear state on successful completion
                            elif ("Order for" in final_response_text and "successfully" in final_response_text) or \
                                 ("Your order" in final_response_text and "Track it here" in final_response_text):
                                session_service.update_session(
                                    app_name=runner.app_name,
                                    user_id=user_id,
                                    session_id=session_id,
                                    data={"state": {
                                        "active_agent": None,
                                        "order_details": {},
                                        "bill_confirmed": False,
                                        "order_status_details": {}
                                    }}
                                )
                        elif event.actions and event.actions.escalate:
                            final_response_text = f"Agent escalated: {event.error_message or 'No details.'}"
                return final_response_text

            final_response_text = await asyncio.get_event_loop().run_in_executor(None, run_generator)
            break
        except Exception as e:
            logger.error(f"Attempt {attempt + 1}/{max_retries} failed: {e}")
            if attempt == max_retries - 1:
                final_response_text = "Error: Agent failed to process request."

    session_service.append_history(
        app_name=runner.app_name,
        user_id=user_id,
        session_id=session_id,
        role="assistant",
        text=final_response_text
    )

    logger.info(f"Agent response for user '{user_id}': '{final_response_text}'")
    return final_response_text

# --- Telegram Handlers ---
async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    logger.info(f"User {user_id} issued /start command")
    await update.message.reply_text(
        "Welcome to Muallim E-commerce! 🌟 I'm your friendly perfume sales assistant. "
        "Ask me about our luxurious perfumes (e.g., 'Show me perfumes for women' or 'Is Oud Al Jannah available?'), "
        "place an order or check your order status. How can I help you today?"
    )

async def agent_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    config: Config,
    session_service: InMemorySessionService,
    runner: Runner,
    logger: logging.Logger
):
    user_id = str(update.effective_user.id)
    query = update.message.text
    session_id = user_id

    logger.info(f"Received message from {user_id}: {query}")
    try:
        response = await call_agent_async(user_id, session_id, query, runner, session_service, logger)
        await update.message.reply_text(response)
        logger.info(f"Sent response to {user_id}: {response}")
    except Exception as e:
        logger.error(f"Error processing query '{query}': {e}")
        await update.message.reply_text("Oops, something went wrong. Try asking about our perfumes, placing an order, checking order status, or cancelling an order!")

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.error(f"Update {update} caused error {context.error}")
    if update and update.message:
        await update.message.reply_text("An error occurred. Please try again!")

# --- Webhook Management ---
async def set_webhook(application: Application, config: Config, logger: logging.Logger) -> bool:
    webhook_url = f"{config.WEBHOOK_URL}/{config.TELEGRAM_API_TOKEN}"
    max_retries = 3

    for attempt in range(max_retries):
        try:
            if await application.bot.set_webhook(webhook_url):
                logger.info(f"Webhook set to: {webhook_url}")
                return True
            logger.warning(f"Webhook set failed on attempt {attempt + 1}")
        except Exception as e:
            logger.warning(f"Webhook attempt {attempt + 1}/{max_retries} failed: {e}")
            if attempt < max_retries - 1:
                await asyncio.sleep(2 ** attempt)
    logger.error("Failed to set webhook after retries")
    return False

# --- Quart App Setup ---
def create_quart_app(config: Config, telegram_app: Application, session_service: InMemorySessionService) -> Quart:
    app = Quart(__name__)

    @app.route('/')
    async def index():
        return "E-commerce Bot is running with webhook!"

    @app.route(f"/{config.TELEGRAM_API_TOKEN}", methods=["POST"])
    async def receive_telegram_update():
        logger = setup_logging()
        try:
            update_data = await request.get_json(force=True)
            if not update_data:
                logger.warning("Empty update received")
                return 'ok', 200
            update = Update.de_json(update_data, telegram_app.bot)
            logger.info(f"Received update: {update}")
            await telegram_app.process_update(update)
            return 'ok', 200
        except Exception as e:
            logger.error(f"Error processing update: {e}")
            return 'error', 500

    @app.route('/sessions/<user_id>', methods=['GET', 'POST'])
    async def check_session(user_id: str):
        logger = setup_logging()
        session_id = user_id
        if request.method == 'POST':
            try:
                await session_service.create_session(app_name=config.APP_NAME, user_id=user_id, session_id=session_id)
                logger.info(f"Created session: {session_id}")
                return {"status": "Session created", "session_id": session_id}
            except Exception as e:
                logger.error(f"Session creation failed: {e}")
                return {"status": "Session creation failed", "error": str(e)}
        try:
            await session_service.get_session(app_name=config.APP_NAME, user_id=user_id, session_id=session_id)
            logger.info(f"Session exists: {session_id}")
            return {"status": "Session exists", "session_id": session_id}
        except KeyError:
            logger.info(f"No session found: {session_id}")
            return {"status": "Session not found", "session_id": session_id}

    @app.route('/sessions/list')
    async def list_sessions():
        logger = setup_logging()
        try:
            sessions = [{"app_name": config.APP_NAME, "user_id": user_id, "session_id": user_id}
                        for user_id in session_service._sessions.keys()
                        if session_service.get_session(app_name=config.APP_NAME, user_id=user_id, session_id=user_id, raise_error=False)]
            logger.info(f"Listed sessions: {sessions}")
            return {"sessions": sessions}
        except Exception as e:
            logger.error(f"Failed to list sessions: {e}")
            return {"status": "Error listing sessions", "error": str(e)}

    return app

# --- Application Setup ---
async def create_telegram_application(config: Config) -> Application:
    app = Application.builder().token(config.TELEGRAM_API_TOKEN).build()
    app.add_handler(CommandHandler("start", start_handler))
    app.add_error_handler(error_handler)
    await app.initialize()
    logger.info("Telegram Application initialized")
    return app

# --- Main Application ---
async def main():
    logger = setup_logging()
    load_dotenv()
    config = Config()
    config.validate()

    try:
        global client, df
        client, df = initialize_google_sheets(config)
        if df.empty:
            logger.error("Failed to initialize DataFrame. Exiting.")
            return

        logger.info("ABOVE AGENT SETUP")

        product_query_agent, order_form_agent, query_refiner_agent, convincing_response_agent = create_agents(df, client)
        order_status_agent = create_order_status_agent()
        root_agent = create_root_agent(config, product_query_agent, order_form_agent, convincing_response_agent, order_status_agent)
        session_service, runner = setup_session_and_runner(config, root_agent)
        logger.info(f"Runner created for agent '{root_agent.name}'")

        telegram_app = await create_telegram_application(config)
        telegram_app.add_handler(MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            lambda update, context: agent_handler(update, context, config, session_service, runner, logger)
        ))

        if config.WEBHOOK_URL:
            if not await set_webhook(telegram_app, config, logger):
                logger.error("Webhook setup failed")
        else:
            logger.info("No WEBHOOK_URL set")

        await telegram_app.start()

        quart_app = create_quart_app(config, telegram_app, session_service)
        await quart_app.run_task(host="0.0.0.0", port=config.PORT, debug=False)

    except Exception as e:
        logger.error(f"Main loop error: {e}")
    finally:
        if 'telegram_app' in locals():
            await telegram_app.stop()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")