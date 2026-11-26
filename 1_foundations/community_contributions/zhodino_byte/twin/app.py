import asyncio
import logging

import gradio as gr
from openai import AsyncOpenAI

import tools as tools_module
from config import MODEL_NAME, OPENROUTER_API_KEY, TELEGRAM_BOT_TOKEN, validate_settings
from context import TWIN_SYSTEM_PROMPT
from styles import CSS, EXAMPLES, JS
from tools import handle_tool_calls, tools
from user_answer import create_bot, dp

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
openai: AsyncOpenAI | None = None

system = [{"role": "system", "content": TWIN_SYSTEM_PROMPT}]
MAX_TOOL_ROUNDS = 8
OWNER_WAITING_MESSAGE = (
    "Мне нужно уточнить это у Андрея. Пожалуйста, подождите — "
    "я покажу его ответ здесь."
)


async def chat(message, history):
    if openai is None:
        raise RuntimeError("OpenAI client has not been initialized")

    messages = system + history + [{"role": "user", "content": message}]
    response = await openai.chat.completions.create(
        model=MODEL_NAME, messages=messages, tools=tools
    )

    waiting_message_shown = False

    for _ in range(MAX_TOOL_ROUNDS):
        if response.choices[0].finish_reason != "tool_calls":
            yield response.choices[0].message.content or ""
            return

        assistant_message = response.choices[0].message
        tool_calls = assistant_message.tool_calls or []
        asks_owner = any(
            tool_call.function.name == "record_unknown_question"
            for tool_call in tool_calls
        )
        if asks_owner and not waiting_message_shown:
            yield OWNER_WAITING_MESSAGE
            waiting_message_shown = True

        results = await handle_tool_calls(tool_calls)
        messages.append(assistant_message.model_dump(exclude_none=True))
        messages.extend(results)
        response = await openai.chat.completions.create(
            model=MODEL_NAME, messages=messages, tools=tools
        )

    raise RuntimeError("The model exceeded the maximum number of tool calls")


async def main():
    global openai

    validate_settings()
    tools_module.main_loop = asyncio.get_running_loop()
    bot = create_bot(TELEGRAM_BOT_TOKEN)
    openai = AsyncOpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=OPENROUTER_API_KEY,
    )

    demo = gr.ChatInterface(
        fn=chat,
        examples=EXAMPLES,
        title="Digital Twin",
        description="Talk to my AI twin about my career",
        chatbot=gr.Chatbot(show_label=False),
    )

    demo.launch(
        prevent_thread_lock=True,
        css=CSS,
        js=JS,
    )
    try:
        await dp.start_polling(bot)
    finally:
        await openai.close()
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
