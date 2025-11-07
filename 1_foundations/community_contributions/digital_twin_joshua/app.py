from dotenv import load_dotenv
from openai import OpenAI
import json
import os
import requests
from pypdf import PdfReader
import gradio as gr


load_dotenv(override=True)


def push(text):
    token = os.getenv("PUSHOVER_TOKEN")
    user = os.getenv("PUSHOVER_USER")
    if not token or not user:
        print("Pushover: Missing PUSHOVER_TOKEN or PUSHOVER_USER", flush=True)
        return
    try:
        response = requests.post(
            "https://api.pushover.net/1/messages.json",
            data={
                "token": token,
                "user": user,
                "message": text,
            },
            timeout=10
        )
        response.raise_for_status()
        print(f"Pushover: Message sent successfully", flush=True)
    except requests.exceptions.RequestException as e:
        print(f"Pushover: Error sending message - {e}", flush=True)
    except Exception as e:
        print(f"Pushover: Unexpected error - {e}", flush=True)


def record_user_details(email, name="Name not provided", notes="not provided"):
    print(f"Tool called: record_user_details(email={email}, name={name}, notes={notes})", flush=True)
    message = f"New contact: {name}\nEmail: {email}\nNotes: {notes}"
    push(message)
    return {"recorded": "ok"}


def record_unknown_question(question):
    print(f"Tool called: record_unknown_question(question={question})", flush=True)
    push(f"Unanswered question: {question}")
    return {"recorded": "ok"}


record_user_details_json = {
    "name": "record_user_details",
    "description": "Use this tool to record that a user is interested in being in touch and provided an email address. Extract the actual email address from the user's message - do not use placeholders like '[email]' or 'email@example.com'. Use the exact email address the user provided.",
    "parameters": {
        "type": "object",
        "properties": {
            "email": {
                "type": "string",
                "description": "The actual email address provided by the user in their message. Extract it exactly as they wrote it. Must be a real email address, not a placeholder."
            },
            "name": {
                "type": "string",
                "description": "The user's name, if they provided it. Use 'Name not provided' if no name was given."
            },
            "notes": {
                "type": "string",
                "description": "Any additional information about the conversation that's worth recording to give context. Use 'not provided' if there's nothing notable."
            }
        },
        "required": ["email"],
        "additionalProperties": False
    }
}


record_unknown_question_json = {
    "name": "record_unknown_question",
    "description": "Always use this tool to record any question that couldn't be answered as you didn't know the answer",
    "parameters": {
        "type": "object",
        "properties": {
            "question": {
                "type": "string",
                "description": "The question that couldn't be answered"
            },
        },
        "required": ["question"],
        "additionalProperties": False
    }
}


tools = [{"type": "function", "function": record_user_details_json},
         {"type": "function", "function": record_unknown_question_json}]


class Me:

    def __init__(self):
        self.openai = OpenAI()
        self.name = "Joshua"

        # Read LinkedIn and Resume PDFs from local me/ directory
        self.linkedin = ""
        self.resume = ""
        try:
            reader = PdfReader("me/linkedin.pdf")
            for page in reader.pages:
                text = page.extract_text()
                if text:
                    self.linkedin += text
        except Exception:
            pass
        try:
            reader_r = PdfReader("me/resume.pdf")
            for page in reader_r.pages:
                text = page.extract_text()
                if text:
                    self.resume += text
        except Exception:
            pass

        with open("me/summary.txt", "r", encoding="utf-8") as f:
            self.summary = f.read()

    def handle_tool_call(self, tool_calls):
        results = []
        for tool_call in tool_calls:
            tool_name = tool_call.function.name
            arguments = json.loads(tool_call.function.arguments)
            print(f"Tool called: {tool_name}", flush=True)
            print(f"Arguments: {arguments}", flush=True)
            tool = globals().get(tool_name)
            result = tool(**arguments) if tool else {}
            results.append({"role": "tool", "content": json.dumps(result), "tool_call_id": tool_call.id})
        return results

    def system_prompt(self):
        system_prompt = f"You are acting as {self.name}. You are answering questions on {self.name}'s website, " \
                        f"particularly questions related to {self.name}'s career, background, skills and experience. " \
                        f"Your responsibility is to represent {self.name} for interactions on the website as faithfully as possible. " \
                        f"You are given a summary, a LinkedIn profile, and a resume which you can use to answer questions. " \
                        f"Be professional and engaging, as if talking to a potential client or future employer who came across the website. " \
                        f"If you don't know the answer to any question, use your record_unknown_question tool to record the question that you couldn't answer. " \
                        f"If the user is engaging in discussion, try to steer them towards getting in touch via email; ask for their email and record it using your record_user_details tool. "

        system_prompt += f"\n\n## Summary:\n{self.summary}\n\n## LinkedIn Profile:\n{self.linkedin}\n\n## Resume:\n{self.resume}\n\n"
        system_prompt += f"With this context, please chat with the user, always staying in character as {self.name}."
        return system_prompt

    def _evaluate_with_anthropic(self, reply, message, history_messages):
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            return {"is_acceptable": True, "feedback": "Evaluator unavailable"}
        rubric = (
            "You are an evaluator that decides whether a response is acceptable. "
            "Judge helpfulness, professionalism, factuality with respect to the provided persona documents, and clarity. "
            "Return JSON with: is_acceptable (true/false) and feedback (1-2 short sentences)."
        )
        convo = json.dumps(history_messages, ensure_ascii=False)
        prompt = (
            f"Conversation so far (JSON array of messages):\n{convo}\n\n"
            f"User message: {message}\n\nAgent reply: {reply}\n\nProvide only the JSON object."
        )
        url = "https://api.anthropic.com/v1/messages"
        headers = {
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }
        payload = {
            "model": "claude-3-7-sonnet-latest",
            "max_tokens": 300,
            "messages": [
                {"role": "system", "content": rubric},
                {"role": "user", "content": prompt},
            ],
        }
        try:
            r = requests.post(url, headers=headers, data=json.dumps(payload), timeout=60)
            r.raise_for_status()
            out = r.json()
            parts = out.get("content", [])
            text = "".join([p.get("text", "") for p in parts if isinstance(p, dict)])
            try:
                data = json.loads(text)
            except Exception:
                data = {"is_acceptable": True, "feedback": text.strip()[:400]}
            if "is_acceptable" not in data:
                data["is_acceptable"] = True
            if "feedback" not in data:
                data["feedback"] = ""
            return data
        except Exception as e:
            return {"is_acceptable": True, "feedback": str(e)}

    def chat(self, message, history):
        base_system = self.system_prompt()
        messages = [{"role": "system", "content": base_system}] + history + [{"role": "user", "content": message}]
        # First attempt
        done = False
        while not done:
            response = self.openai.chat.completions.create(model="gpt-4o-mini", messages=messages, tools=tools)
            if response.choices[0].finish_reason == "tool_calls":
                tool_msg = response.choices[0].message
                tool_calls = tool_msg.tool_calls
                results = self.handle_tool_call(tool_calls)
                messages.append(tool_msg)
                messages.extend(results)
            else:
                done = True
        reply = response.choices[0].message.content

        # Evaluate and optionally retry up to 2 times
        eval_history = [m for m in messages if m["role"] in ("system", "user", "assistant", "tool")]
        evaluation = self._evaluate_with_anthropic(reply, message, eval_history)
        attempts = 0
        while not evaluation.get("is_acceptable", True) and attempts < 2:
            attempts += 1
            improved_system = base_system + (
                "\n\n## Previous answer rejected\n"
                f"Your previous answer was:\n{reply}\n\n"
                f"Reason for rejection (from evaluator):\n{evaluation.get('feedback','')}\n\n"
                "Revise your answer to address the feedback while staying faithful to the provided documents."
            )
            messages = [{"role": "system", "content": improved_system}] + history + [{"role": "user", "content": message}]
            done = False
            while not done:
                response = self.openai.chat.completions.create(model="gpt-4o-mini", messages=messages, tools=tools)
                if response.choices[0].finish_reason == "tool_calls":
                    tool_msg = response.choices[0].message
                    tool_calls = tool_msg.tool_calls
                    results = self.handle_tool_call(tool_calls)
                    messages.append(tool_msg)
                    messages.extend(results)
                else:
                    done = True
            reply = response.choices[0].message.content
            eval_history = [m for m in messages if m["role"] in ("system", "user", "assistant", "tool")]
            evaluation = self._evaluate_with_anthropic(reply, message, eval_history)

        return reply


if __name__ == "__main__":
    me = Me()
    gr.ChatInterface(me.chat, type="messages").launch()


