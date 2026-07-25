import json
import os
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI
from pydantic import BaseModel
from pypdf import PdfReader


load_dotenv(override=True)


class EvaluateAnswer(BaseModel):
    """Structured output for evaluating whether an LLM response has enough context."""

    feedback: str
    hasEnoughContext: bool


class Profiler:
    """
    An AI-powered personal profiler that answers questions about my
    career, background, skills and experience using my resume and summary.

    It includes a self-evaluation loop that retries responses that lack
    sufficient quality, and tool-call support for capturing interested leads
    and recording unanswered questions.
    """

    DEFAULT_MODEL = "gpt-4o-mini"

    def __init__(
        self,
        name: str,
        profile_path: Path | None = None,
        model: str = DEFAULT_MODEL,
    ):
        self.name = name
        self.model = model
        self.profile_path = profile_path or Path(__file__).parent / "profile"
        if os.getenv("OPENAI_API_KEY"):
            self.openai = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        else:
            raise ValueError("OPENAI_API_KEY not found in environment variables")

        self.profile = self.read_profile()
        self.summary = self.read_summary()
        self.system_prompt = self.build_system_prompt()
        self.evaluate_system_prompt = self.build_evaluate_system_prompt()
        self.tools = self.build_tools()

    def read_profile(self) -> str:
        """Extract text from all PDF files found in the profile directory."""
        text = ""
        if self.profile_path.exists():
            for pdf_file in self.profile_path.glob("*.pdf"):
                reader = PdfReader(pdf_file)
                for page in reader.pages:
                    text += page.extract_text() or ""
        return text

    def read_summary(self) -> str:
        """Read all plain-text summary files found in the profile directory."""
        text = ""
        if self.profile_path.exists():
            for txt_file in self.profile_path.glob("*.txt"):
                text += txt_file.read_text(encoding="utf-8")
        return text

    def build_system_prompt(self) -> str:
        prompt = (
            f"You are acting as {self.name} who is also known as Eben. "
            f"You are answering questions on {self.name}'s Profile, particularly "
            f"questions related to {self.name}'s career, background, skills and experience. "
            f"Your responsibility is to represent {self.name} for interactions concerning "
            f"him as faithfully as possible. "
            f"You are given a summary of {self.name}'s background and Resume profile which "
            f"you can use to answer questions. "
            "Be professional and engaging, as if talking to a potential client or future "
            "employer who came across the profile. "
            "If you don't know the answer to any question, use your record_unknown_question "
            "tool to record the question that you couldn't answer, even if it's about "
            "something trivial or unrelated to career. "
            "If the user is engaging in discussion, try to steer them towards getting in "
            "touch via email; ask for their email and record it using your "
            "record_user_details tool."
        )
        prompt += f"\n\n## Summary:\n{self.summary}\n\n## Resume:\n{self.profile}\n\n"
        prompt += (
            f"With this context, please chat with the user, always staying in character "
            f"as {self.name}."
        )
        return prompt

    def build_evaluate_system_prompt(self) -> str:
        prompt = (
            "You are an evaluator that decides whether a response to a question is acceptable. "
            "You are provided with a conversation between a User and an Agent. Your task is to "
            "decide whether the Agent's latest response is acceptable quality. "
            f"The Agent is playing the role of {self.name} and is representing {self.name} "
            "on their profile. "
            "The Agent has been instructed to be professional and engaging, as if talking to "
            "a potential client or future employer who came across the profile. "
            f"The Agent has been provided with context on {self.name} in the form of their "
            "summary and resume details. Here's the information:"
        )
        prompt += f"\n\n## Summary:\n{self.summary}\n\n## Resume:\n{self.profile}\n\n"
        prompt += (
            "With this context, please evaluate the latest response, replying with whether "
            "the response is acceptable and your feedback."
        )
        return prompt

    def build_tools(self) -> list[dict]:
        record_user_details = {
            "name": "record_user_details",
            "description": (
                "Use this tool to record that a user is interested in being in touch "
                "and provided an email address"
            ),
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
                        "description": (
                            "Any additional information about the conversation "
                            "that's worth recording to give context"
                        ),
                    },
                },
                "required": ["email"],
                "additionalProperties": False,
            },
        }

        record_unknown_question = {
            "name": "record_unknown_question",
            "description": (
                "Always use this tool to record any question that couldn't be answered "
                "as you didn't know the answer"
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

        return [
            {"type": "function", "function": record_user_details},
            {"type": "function", "function": record_unknown_question},
        ]

    def record_user_details(
        self, email: str, name: str | None = None, notes: str | None = None
    ) -> dict:
        """Persist a lead's contact details to a local file."""
        entry = {"email": email}
        if name:
            entry["name"] = name
        if notes:
            entry["notes"] = notes

        leads_file = self.profile_path / "leads.jsonl"
        with open(leads_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")

        print(f"Lead recorded: {entry}", flush=True)
        return {"status": "recorded", **entry}

    def record_unknown_question(self, question: str) -> dict:
        """Persist an unanswered question to a local file for later review."""
        questions_file = self.profile_path / "unknown_questions.jsonl"
        with open(questions_file, "a", encoding="utf-8") as f:
            f.write(json.dumps({"question": question}) + "\n")

        print(f"Unknown question recorded: {question}", flush=True)
        return {"status": "recorded", "question": question}

    def dispatch_tool(self, tool_name: str, arguments: dict) -> dict:
        """Route a tool call to the appropriate method on this instance."""
        handler = getattr(self, tool_name, None)
        if handler is None:
            print(f"Warning: unknown tool '{tool_name}'", flush=True)
            return {}
        return handler(**arguments)

    def handle_tool_calls(self, tool_calls) -> list[dict]:
        results = []
        for tool_call in tool_calls:
            tool_name = tool_call.function.name
            arguments = json.loads(tool_call.function.arguments)
            print(f"Tool called: {tool_name}", flush=True)
            result = self.dispatch_tool(tool_name, arguments)
            results.append(
                {
                    "role": "tool",
                    "content": json.dumps(result),
                    "tool_call_id": tool_call.id,
                }
            )
        return results

    def evaluate_user_prompt(self, reply: str, message: str, history: list) -> str:
        prompt = (
            f"Here's the conversation between the User and the Agent:\n\n{history}\n\n"
        )
        prompt += f"Here's the latest message from the User:\n\n{message}\n\n"
        prompt += f"Here's the latest response from the Agent:\n\n{reply}\n\n"
        prompt += "Please evaluate the response, replying with whether it is acceptable and your feedback."
        return prompt

    def evaluate(self, reply: str, message: str, history: list) -> EvaluateAnswer:
        messages = [
            {"role": "system", "content": self.evaluate_system_prompt},
            {
                "role": "user",
                "content": self.evaluate_user_prompt(reply, message, history),
            },
        ]
        response = self.openai.chat.completions.parse(
            model=self.model, messages=messages, response_format=EvaluateAnswer
        )
        return response.choices[0].message.parsed

    def rerun_answer(self, reply: str, message: str, history: list, feedback: str):
        """Regenerate a response after it failed quality evaluation."""
        updated_system_prompt = (
            self.system_prompt + "\n\n## Previous answer rejected\n"
            "You just tried to reply, but the quality control rejected your reply\n"
            f"## Your attempted answer:\n{reply}\n\n"
            f"## Reason for rejection:\n{feedback}\n\n"
        )
        messages = (
            [{"role": "system", "content": updated_system_prompt}]
            + history
            + [{"role": "user", "content": message}]
        )
        response = self.openai.chat.completions.create(
            model=self.model, messages=messages, stream=True
        )
        result = ""
        for chunk in response:
            result += chunk.choices[0].delta.content or ""
            yield result

    def chat(self, message: str, history: list):
        """
        Process a user message and yield a streaming response.

        Implements a tool-call loop followed by a self-evaluation step that
        retries the response once if quality is deemed insufficient.
        """
        messages = (
            [{"role": "system", "content": self.system_prompt}]
            + history
            + [{"role": "user", "content": message}]
        )

        # Resolve any tool calls before streaming the final reply
        while True:
            response = self.openai.chat.completions.create(
                model=self.model, messages=messages, tools=self.tools
            )
            finish_reason = response.choices[0].finish_reason

            if finish_reason == "tool_calls":
                tool_message = response.choices[0].message
                tool_results = self.handle_tool_calls(tool_message.tool_calls)
                messages.append(tool_message)
                messages.extend(tool_results)
            else:
                break

        # Stream the final reply
        stream = self.openai.chat.completions.create(
            model=self.model, messages=messages, stream=True
        )
        result = ""
        for chunk in stream:
            result += chunk.choices[0].delta.content or ""
            yield result

        # Evaluate quality and retry once if it falls short
        evaluation = self.evaluate(result, message, history)
        if evaluation.hasEnoughContext:
            print("Passed evaluation - returning reply", flush=True)
        else:
            print(f"Failed evaluation - retrying\n{evaluation.feedback}", flush=True)
            yield from self.rerun_answer(result, message, history, evaluation.feedback)
