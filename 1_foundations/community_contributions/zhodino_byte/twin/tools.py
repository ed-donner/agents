import asyncio
import json
import logging

from config import OWNER_REPLY_TIMEOUT_SECONDS, TELEGRAM_CHAT_ID
from human_bridge import register_question, remove_question
from user_answer import get_bot

main_loop = None
logger = logging.getLogger(__name__)


async def push(text):
    bot = get_bot()
    coroutine = bot.send_message(TELEGRAM_CHAT_ID, text=text)
    current_loop = asyncio.get_running_loop()

    if main_loop is not None and current_loop is not main_loop:
        future = asyncio.run_coroutine_threadsafe(coroutine, main_loop)
        return await asyncio.wrap_future(future)
    return await coroutine


async def record_user_details(email, name="Name not provided", notes="not provided"):
    await push(f"Recording interest from {name} with email {email} and notes {notes}")
    return "OK"


async def record_unknown_question(question):
    sent_message = await push(
        "Посетитель сайта задал вопрос, на который агент не знает ответа:\n\n"
        f"{question}\n\n"
        "Чтобы ответить посетителю, используйте Reply на это сообщение."
    )
    answer_future = asyncio.get_running_loop().create_future()
    register_question(sent_message.message_id, answer_future)

    try:
        answer = await asyncio.wait_for(
            answer_future,
            timeout=OWNER_REPLY_TIMEOUT_SECONDS,
        )
        return f"The owner answered: {answer}"
    except asyncio.TimeoutError:
        return (
            "The owner did not reply before the waiting period ended. "
            "Tell the visitor that the answer is not available yet."
        )
    finally:
        remove_question(sent_message.message_id)


record_user_details_json = {
    "name": "record_user_details",
    "description": "Use this tool to record that a user is interested in being in touch and provided an email address",
    "parameters": {
        "type": "object",
        "properties": {
            "email": {
                "type": "string",
                "description": "The email address of this user",
            },
            "name": {
                "type": "string",
                "description": "The user's name, if they provided it",
            },
            "notes": {
                "type": "string",
                "description": "Any additional info about the conversation that's worth recording to give context",
            },
        },
        "required": ["email"],
        "additionalProperties": False,
    },
}

record_unknown_question_json = {
    "name": "record_unknown_question",
    "description": (
        "Use this tool when you do not know an answer. It asks the owner in "
        "Telegram, waits for their reply, and returns their answer."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "question": {
                "type": "string",
                "description": "The question that couldn't be answered",
            },
        },
        "required": ["question"],
        "additionalProperties": False,
    },
}

tools = [
    {"type": "function", "function": record_user_details_json},
    {"type": "function", "function": record_unknown_question_json},
]

tool_map = {
    "record_user_details": record_user_details,
    "record_unknown_question": record_unknown_question,
}


async def handle_tool_calls(tool_calls):
    results = []
    for tool_call in tool_calls:
        tool_name = tool_call.function.name
        try:
            arguments = json.loads(tool_call.function.arguments)
        except json.JSONDecodeError as error:
            result = f"Invalid tool arguments: {error}"
            logger.warning("Invalid arguments for tool %s: %s", tool_name, error)
            arguments = None

        tool = tool_map.get(tool_name)
        if arguments is None:
            pass
        elif tool is None:
            result = "Unknown tool: " + tool_name
        else:
            try:
                result = await tool(**arguments)
            except Exception as error:
                logger.exception("Tool %s failed", tool_name)
                result = f"The notification could not be recorded: {error}"

        results.append(
            {
                "role": "tool",
                "content": json.dumps(result, ensure_ascii=False),
                "tool_call_id": tool_call.id,
            }
        )
    return results
