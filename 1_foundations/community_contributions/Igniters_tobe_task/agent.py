"""
Bio Agent — Core Agent
-----------------------
Orchestrates the agent loop, tool dispatch, evaluation, and reflection.
This is the central class that ties everything together.
"""

import inspect
import json

from openai import OpenAI

import database
import rag
import evaluator
from tools import TOOLS_LIST, TOOLS_MAP
from config import (
    OLLAMA_BASE_URL,
    OLLAMA_API_KEY,
    AGENT_MODEL,
    EVAL_ACCEPT_SCORE,
    EVAL_FAQ_SCORE,
    MAX_EVAL_RETRIES,
)


class BioAgent:
    """
    A self-improving career assistant that:
    1. Checks FAQ cache before doing expensive LLM + RAG calls
    2. Searches a ChromaDB knowledge base for factual answers
    3. Evaluates its own responses via a separate LLM judge
    4. Refines responses that score below threshold (reflection)
    5. Promotes excellent answers to FAQ for future reuse
    """

    def __init__(self):
        self._client = OpenAI(base_url=OLLAMA_BASE_URL, api_key=OLLAMA_API_KEY)

        # Initialise database tables
        database.init_db()

        # Ingest knowledge base (idempotent — skips if already done)
        chunk_count = rag.ingest_knowledge()
        print(f"[BioAgent] Knowledge base ready — {chunk_count} chunks indexed.")

    # ── System Prompt ─────────────────────────────────────────────────

    def _system_prompt(self) -> str:
        return """You are acting as a professional career assistant, representing the person described in the knowledge base. You answer questions on their behalf — about their career, skills, experience, projects, and professional background.

## Your Workflow
1. **ALWAYS call `lookup_faq` first** with the user's question. If a cached answer exists, use it directly.
2. If no FAQ match, call `search_knowledge_base` with a relevant query to retrieve factual context.
3. Use the retrieved context to craft an accurate, professional response.
4. If a user shares their email or wants to connect, call `record_contact` to save their details.

## Rules
- Stay in character at all times — you ARE this professional person.
- Only state facts that come from the knowledge base or FAQ. Do not fabricate details.
- Be warm, professional, and engaging — as if speaking to a potential employer or collaborator.
- If you cannot find an answer in the knowledge base, say so honestly rather than guessing.
- Gently steer conversations toward professional topics and encourage users to get in touch.
"""

    # ── Tool Dispatch ─────────────────────────────────────────────────

    def _handle_tool_calls(self, tool_calls) -> tuple[list[dict], str]:
        """
        Execute tool calls and return (results_messages, last_context).
        Captures RAG context for the evaluator.
        """
        results = []
        context = ""

        for tool_call in tool_calls:
            name = tool_call.function.name
            args = json.loads(tool_call.function.arguments)

            print(f"  [Tool] {name}({args})")

            func = TOOLS_MAP.get(name)
            if func:
                # Filter args to only parameters the function accepts.
                # Small LLMs sometimes hallucinate extra keys.
                sig = inspect.signature(func)
                valid_params = set(sig.parameters.keys())
                filtered_args = {k: v for k, v in args.items() if k in valid_params}

                if filtered_args != args:
                    dropped = set(args.keys()) - valid_params
                    print(f"  [Warning] Dropped unexpected args: {dropped}")

                result = func(**filtered_args)
                # Capture RAG context for evaluation
                if name == "search_knowledge_base":
                    context = result
            else:
                result = json.dumps({"error": f"Unknown tool: {name}"})

            results.append({
                "role": "tool",
                "content": result if isinstance(result, str) else json.dumps(result),
                "tool_call_id": tool_call.id,
            })

        return results, context

    # ── Agent Loop ────────────────────────────────────────────────────

    def _run_agent_loop(self, messages: list[dict]) -> tuple[str, str]:
        """
        Run the while-not-done agent loop.
        Returns (agent_answer, rag_context_used).
        """
        context = ""

        while True:
            response = self._client.chat.completions.create(
                model=AGENT_MODEL,
                messages=messages,
                tools=TOOLS_LIST,
            )

            choice = response.choices[0]

            if choice.finish_reason == "tool_calls":
                message = choice.message
                tool_calls = message.tool_calls
                tool_results, tool_context = self._handle_tool_calls(tool_calls)

                if tool_context:
                    context = tool_context

                messages.append(message)
                messages.extend(tool_results)
            else:
                # LLM produced a final text response
                return choice.message.content or "", context

    # ── Public Chat Interface ─────────────────────────────────────────

    def chat(self, message: str, history: list[dict]) -> str:
        """
        Main entry point for Gradio. Handles:
        1. Agent loop (tool calling + response generation)
        2. Evaluation (LLM-as-judge scoring)
        3. Reflection (retry if score < threshold)
        4. Persistence (log conversation, promote to FAQ)
        """
        messages = (
            [{"role": "system", "content": self._system_prompt()}]
            + history
            + [{"role": "user", "content": message}]
        )

        answer = ""
        context = ""
        score = 0

        for attempt in range(1 + MAX_EVAL_RETRIES):
            answer, loop_context = self._run_agent_loop(messages)
            if loop_context:
                context = loop_context

            # Evaluate the response
            eval_result = evaluator.evaluate_response(
                user_question=message,
                agent_answer=answer,
                context=context,
            )
            score = eval_result["score"]
            feedback = eval_result["feedback"]

            print(f"  [Eval] Attempt {attempt + 1} — Score: {score}/10 — {feedback}")

            if score >= EVAL_ACCEPT_SCORE:
                break  # Good enough — accept

            # Reflection: feed evaluator feedback back and retry
            messages.append({"role": "assistant", "content": answer})
            messages.append({
                "role": "user",
                "content": (
                    f"Your previous response scored {score}/10. "
                    f"Evaluator feedback: {feedback}\n\n"
                    "Please improve your response based on this feedback."
                ),
            })
            print(f"  [Reflection] Retrying with evaluator feedback...")

        # ── Persist Results ───────────────────────────────────────────

        # Always log the conversation
        database.log_conversation(
            user_question=message,
            agent_answer=answer,
            eval_score=score,
        )

        # Promote excellent answers to FAQ
        if score >= EVAL_FAQ_SCORE:
            database.save_faq(question=message, answer=answer)
            print(f"  [FAQ] Answer promoted to FAQ (score {score})")

        return answer
