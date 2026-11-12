import json
import logging
import re
from functools import lru_cache

from openai import OpenAI
from context import build_chat_context, GET_EVALUATOR_PROMPT
from tools import tools, handle_tool_calls, record_unknown_question, TOOL_SUCCESS_RESULTS
from dotenv import load_dotenv

load_dotenv(override=True)

MODEL_NAME = "gpt-5.4-mini"
MODEL_EVALUATOR_NAME = "gpt-5.4-nano"
MAX_TOOL_ROUNDS = 5
MAX_REVISIONS = 2
logger = logging.getLogger(__name__)

FALLBACK_MESSAGES = {
    "en": "Sorry, I can't answer that question right now.",
    "es": "Lo siento, por ahora no puedo responder esa pregunta.",
}
SCOPE_MESSAGES = {
    "en": "I can only answer questions about Karina's professional background, skills, and work.",
    "es": "Solo puedo responder preguntas sobre la trayectoria, habilidades y experiencia profesional de Karina.",
}
CONTACT_CONFIRMATIONS = {
    "en": "Thank you. I've recorded your email so Karina can get in touch with you.",
    "es": "Gracias. He registrado tu correo para que Karina pueda contactarte.",
}
EXISTING_CONTACT_CONFIRMATIONS = {
    "en": "Your email is already registered. No new notification was sent.",
    "es": "Tu correo ya está registrado. No se envió otra notificación.",
}


def tool_succeeded(tool_cache, name):
    accepted = {json.dumps(result) for result in TOOL_SUCCESS_RESULTS.get(name, set())}
    return any(tool_name == name and result in accepted
               for (tool_name, _), result in tool_cache.items())


def extract_emails(text):
    return re.findall(r"[\w.+-]+@[\w.-]+\.[a-zA-Z]{2,}", text)


def contact_results(tool_cache):
    results = {}
    for (name, arguments), result in tool_cache.items():
        if name == "record_user_details":
            email = json.loads(arguments)["email"].strip().lower()
            # A later duplicate lookup must not hide a new successful registration.
            if results.get(email) != json.dumps("OK"):
                results[email] = result
    return results


def contact_confirmation(tool_cache, language, message=""):
    language = language if language in CONTACT_CONFIRMATIONS else "en"
    results = contact_results(tool_cache)
    for email in extract_emails(message):
        results.setdefault(email.strip().lower(), None)
    if len(results) > 1:
        groups = [
            (json.dumps("OK"), {"en": "Registered emails", "es": "Correos registrados"}),
            (json.dumps("Email already exists"), {"en": "Already registered", "es": "Ya estaban registrados"}),
            (None, {"en": "Not registered", "es": "No se registraron"}),
        ]
        return "\n\n".join(
            f"{labels[language]}: {', '.join(emails)}."
            for status, labels in groups
            if (emails := [email for email, result in results.items() if result == status])
        )
    already_exists = any(name == "record_user_details" and result == json.dumps("Email already exists")
                         for (name, _), result in tool_cache.items())
    messages = EXISTING_CONTACT_CONFIRMATIONS if already_exists else CONTACT_CONFIRMATIONS
    return messages.get(language, messages["en"])


EVALUATION_FORMAT = {
    "type": "json_schema",
    "json_schema": {
        "name": "response_evaluation",
        "strict": True,
        "schema": {
            "type": "object",
            "properties": {
                "approved": {"type": "boolean"},
                "out_of_scope": {"type": "boolean"},
                "feedback": {"type": "string"},
            },
            "required": ["approved", "out_of_scope", "feedback"],
            "additionalProperties": False,
        },
    },
}


@lru_cache(maxsize=1)
def get_client():
    return OpenAI()


def evaluate_response(user_message, assistant_response, language="en"):
    response = get_client().chat.completions.create(
        model=MODEL_EVALUATOR_NAME,
        messages=[
            {"role": "system", "content": GET_EVALUATOR_PROMPT(language)},
            {"role": "user", "content": json.dumps({
                "user_message": user_message,
                "assistant_response": assistant_response,
            }, ensure_ascii=False)},
        ],
        response_format=EVALUATION_FORMAT,
    )
    choice = response.choices[0]
    if choice.finish_reason == "stop" and not choice.message.refusal:
        try:
            evaluation = json.loads(choice.message.content or "")
            if (isinstance(evaluation, dict)
                    and type(evaluation.get("approved")) is bool
                    and type(evaluation.get("out_of_scope")) is bool
                    and isinstance(evaluation.get("feedback"), str)):
                return evaluation
        except (ValueError, TypeError):
            pass
    raise RuntimeError("The evaluator did not return a valid evaluation. Please try again.")


def generate_response(messages, tool_cache, user_message):
    """Process tools on both initial responses and evaluator revisions."""
    for round_number in range(MAX_TOOL_ROUNDS + 1):
        response = get_client().chat.completions.create(
            model=MODEL_NAME, messages=messages, tools=tools,
        )
        choice = response.choices[0]
        assistant_message = choice.message
        if assistant_message.tool_calls:
            if round_number == MAX_TOOL_ROUNDS:
                raise RuntimeError("Too many tool calls. Please try a simpler question.")
            serialized_message = assistant_message.model_dump(exclude_none=True)
            messages.append(serialized_message)
            for index, tool_call in enumerate(assistant_message.tool_calls):
                arguments = json.loads(tool_call.function.arguments)
                tool_name = tool_call.function.name
                if tool_name not in {"record_user_details", "record_unknown_question"}:
                    raise ValueError("Unsupported tool")
                if not isinstance(arguments, dict):
                    raise ValueError("Tool arguments must be an object")
                if tool_name == "record_user_details":
                    # Only user-provided addresses may be sent to the contact tool.
                    provided_emails = {
                        email for entry in messages if entry.get("role") == "user"
                        for email in extract_emails(entry["content"])
                    }
                    if arguments.get("email") not in provided_emails:
                        raise ValueError("Contact email was not provided by the visitor")
                if tool_name == "record_unknown_question":
                    # Record the actual visitor question, not a model paraphrase.
                    arguments = {"question": user_message}
                    tool_call = tool_call.model_copy(update={"function":
                        tool_call.function.model_copy(update={
                            "arguments": json.dumps(arguments),
                        })})
                    serialized_message["tool_calls"][index]["function"]["arguments"] = tool_call.function.arguments
                # Revisions may request the same notification again. Execute
                # identical calls only once within this visitor turn.
                key = (tool_call.function.name, json.dumps(
                    arguments, sort_keys=True,
                ))
                if key not in tool_cache:
                    try:
                        result = handle_tool_calls([tool_call])[0]["content"]
                        if json.loads(result) not in TOOL_SUCCESS_RESULTS[tool_name]:
                            raise RuntimeError("Tool did not confirm success")
                        tool_cache[key] = result
                    except Exception:
                        tool_cache[key] = None
                        raise
                messages.append({
                    "role": "tool", "content": tool_cache[key],
                    "tool_call_id": tool_call.id,
                })
            if tool_succeeded(tool_cache, "record_user_details"):
                completed = {email for email, result in contact_results(tool_cache).items()
                             if result is not None}
                pending = {email.strip().lower() for email in extract_emails(user_message)} - completed
                if not pending:
                    # Let the caller acknowledge the verified actions directly.
                    return None
            continue
        if choice.finish_reason != "stop" or not assistant_message.content:
            raise RuntimeError("No complete response was generated. Please try again.")
        return assistant_message.content


def record_question_once(message, tool_cache):
    key = ("record_unknown_question", json.dumps({"question": message}, sort_keys=True))
    if key in tool_cache:
        return tool_cache[key] is not None
    try:
        result = record_unknown_question(message)
        if result != "OK":
            raise RuntimeError("Question notification did not confirm success")
        tool_cache[key] = json.dumps(result)
        return True
    except Exception as exc:
        tool_cache[key] = None
        logger.warning("Question notification failed (%s)", type(exc).__name__)
        return False


def fallback_response(message, language, tool_cache, out_of_scope=False):
    language = language if language in FALLBACK_MESSAGES else "en"
    if tool_succeeded(tool_cache, "record_user_details"):
        # A later evaluation/API failure must not hide a completed contact action.
        return contact_confirmation(tool_cache, language, message)
    text = SCOPE_MESSAGES[language] if out_of_scope else FALLBACK_MESSAGES[language]
    if record_question_once(message, tool_cache):
        status = {"en": "Your question has been recorded.",
                  "es": "Tu pregunta ha sido registrada."}
    else:
        status = {"en": "I couldn't record your question. Please try again later.",
                  "es": "No pude registrar tu pregunta. Inténtalo de nuevo más tarde."}
    return f"{text} {status[language]}"


def normalize_history(history):
    """Convert Gradio 6 text blocks to plain API messages, dropping UI fields."""
    messages = []
    for entry in history or []:
        role = entry.get("role")
        if role not in ("user", "assistant"):
            continue
        content = entry.get("content")
        if isinstance(content, list):
            content = "\n".join(
                block if isinstance(block, str) else block["text"]
                for block in content
                if isinstance(block, str) or (
                    isinstance(block, dict) and block.get("type") == "text"
                    and isinstance(block.get("text"), str)
                )
            )
        if isinstance(content, str) and content:
            messages.append({"role": role, "content": content})
    return messages


def _chat(message, history, language, tool_cache):
    history = normalize_history(history)
    context = build_chat_context(message, history, language)
    messages = [{"role": "system", "content": context}] + list(history) + [
        {"role": "user", "content": message},
    ]
    for revision in range(MAX_REVISIONS + 1):
        candidate = generate_response(messages, tool_cache, message)
        if tool_succeeded(tool_cache, "record_user_details"):
            return contact_confirmation(tool_cache, language, message)
        evaluation = evaluate_response(message, candidate, language)
        if evaluation["out_of_scope"]:
            return fallback_response(message, language, tool_cache, out_of_scope=True)
        if evaluation["approved"]:
            return candidate
        logger.warning("Evaluator rejected response (attempt=%d/%d, feedback=%s)",
                       revision + 1, MAX_REVISIONS + 1, evaluation["feedback"])
        if revision < MAX_REVISIONS:
            messages.extend([
                {"role": "assistant", "content": candidate},
                {"role": "system", "content": (
                    "Revise the candidate using this evaluator feedback. "
                    "Keep following the original professional scope, source "
                    "context, and selected response language. Do not repeat actions "
                    "that already succeeded.\n" + evaluation["feedback"]
                )},
            ])
    return fallback_response(message, language, tool_cache)


def chat(message, history, language="en"):
    tool_cache = {}
    try:
        return _chat(message, history, language, tool_cache)
    except Exception as exc:
        # Gradio must receive an answer even when a model, tool, or resource fails.
        body = getattr(exc, "body", None)
        error = body.get("error", body) if isinstance(body, dict) else {}
        param = error.get("param") if isinstance(error, dict) else None
        logger.warning("Chat response failed (%s, status=%s, param=%s)",
                       type(exc).__name__, getattr(exc, "status_code", None), param)
        return fallback_response(message, language, tool_cache)


def build_demo():
    import gradio as gr
    from styles import EXAMPLES

    with gr.Blocks() as demo:
        gr.Markdown("# Digital Twin\nTalk to my AI twin about my career")
        language = gr.Dropdown(
            choices=[("English", "en"), ("Español", "es")],
            value="en",
            label="Response language / Idioma de respuesta",
            interactive=True,
            allow_custom_value=False,
        )
        textbox = gr.Textbox(placeholder="Ask about my career…", render=False)
        gr.ChatInterface(
            chat,
            additional_inputs=[language],
            textbox=textbox,
            chatbot=gr.Chatbot(show_label=False),
        )
        # Examples fill only the message, preserving the selected language.
        gr.Examples(examples=EXAMPLES, inputs=textbox)
    return demo


if __name__ == "__main__":
    import gradio as gr
    from styles import CSS, JS

    build_demo().launch(css=CSS, js=JS, theme=gr.themes.Base())
