import os
import json
import re
from typing import Annotated, List, Any, Optional, Dict
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from dotenv import load_dotenv
from langgraph.prebuilt import ToolNode
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
from pydantic import BaseModel, Field
from analyst_tools import (
    get_analyst_tools,
    get_session_sandbox_dir,
    normalize_message_text,
    build_notebook,
    build_html_report,
    extract_python_snippets,
    collect_charts,
    recover_orphaned_charts,
)
import uuid
import logging
from datetime import datetime
load_dotenv(override=True)
logger = logging.getLogger(__name__)

class State(TypedDict):
    messages: Annotated[List[Any], add_messages]
    success_criteria: str
    dataset_filename: Optional[str]        # filename inside sandbox/
    session_dir: str
    feedback_on_work: Optional[str]
    success_criteria_met: bool
    user_input_needed: bool
    max_iterations: int
    iteration_count: int
    max_worker_turns: int
    worker_turn_count: int
    tool_calls_made: List[str]
    tool_outputs_observed: List[str]
    
class EvaluatorOutput(BaseModel):
    feedback: str = Field(
        description="Detailed feedback on the analyst's response"
    )
    success_criteria_met: bool = Field(
        description="True only when the success criteria are fully met"
    )
    user_input_needed: bool = Field(
        description=(
            "True if the analyst needs user clarification, is stuck, "
            "or the task cannot proceed without more information"
        )
    )
    insights_are_non_trivial: bool = Field(
        description=(
            "True if the insights go beyond trivial descriptive stats "
            "(e.g. include correlations, anomalies, trends, or recommendations)"
        )
    )

class DataAnalystAgent:
    def __init__(self, max_iterations: int = 3, max_worker_turns: int = 12):
        self.graph = None
        self.tools = None
        self._tool_node = None
        self.worker_llm_with_tools = None
        self.evaluator_llm = None
        self.agent_id = str(uuid.uuid4())
        self.session_dir = str(get_session_sandbox_dir(self.agent_id))
        self.max_iterations = max_iterations
        self.max_worker_turns = max_worker_turns
        self.memory = MemorySaver()
    def _build_llm(self, *, evaluator: bool = False) -> ChatOpenAI:
        using_openrouter = bool(os.getenv("OPENROUTER_API_KEY"))
        if using_openrouter:
            model = os.getenv(
                "OPENROUTER_EVALUATOR_MODEL" if evaluator else "OPENROUTER_MODEL",
                "anthropic/claude-3.7-sonnet",
            )
            reasoning = {"exclude": True}
            reasoning_effort = os.getenv("OPENROUTER_REASONING_EFFORT")
            reasoning_max_tokens = os.getenv("OPENROUTER_REASONING_MAX_TOKENS")
            if reasoning_max_tokens:
                reasoning["max_tokens"] = int(reasoning_max_tokens)
            elif reasoning_effort:
                reasoning["effort"] = reasoning_effort
            elif not evaluator:
                reasoning["max_tokens"] = 2048
            return ChatOpenAI(
                model=model,
                api_key=os.getenv("OPENROUTER_API_KEY"),
                base_url=os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"),
                default_headers={
                    "HTTP-Referer": os.getenv("OPENROUTER_SITE_URL", "http://localhost:7860"),
                    "X-Title": os.getenv("OPENROUTER_APP_NAME", "Data Analyst Agent"),
                },
                reasoning=reasoning,
            )
        model = os.getenv(
            "OPENAI_EVALUATOR_MODEL" if evaluator else "OPENAI_MODEL",
            "gpt-4o-mini",
        )
        return ChatOpenAI(model=model)
    def setup(self):
        self.tools = get_analyst_tools(self.session_dir)
        worker_llm = self._build_llm(evaluator=False)
        self.worker_llm_with_tools = worker_llm.bind_tools(self.tools)
        self.evaluator_llm = self._build_llm(evaluator=True)
        self.build_graph()
   
    def _is_python_tool(self, tool_name: str) -> bool:
        return "python" in (tool_name or "").lower()
    def worker(self, state: State) -> Dict[str, Any]:
        next_worker_turn = state.get("worker_turn_count", 0) + 1
        if next_worker_turn > state["max_worker_turns"]:
            return {
                "messages": [
                    AIMessage(
                        content=(
                            "I could not complete the analysis within the allowed tool-execution "
                            "limit. Please refine the request or inspect the dataset manually."
                        )
                    )
                ],
                "worker_turn_count": next_worker_turn,
            }
        session_dir = state["session_dir"].replace("\\", "/")
        tool_calls_made = state.get("tool_calls_made", [])
        tool_outputs_observed = state.get("tool_outputs_observed", [])
        python_already_used = any(self._is_python_tool(name) for name in (tool_calls_made + tool_outputs_observed))
        dataset_hint = ""
        if state.get("dataset_filename"):
            if python_already_used:
                dataset_hint = f"""
A dataset has been uploaded by the user and you have already used Python to inspect it.
It is available in the session sandbox directory as: {state['dataset_filename']}
Its full path for Python code is: {session_dir}/{state['dataset_filename']}
You have already gathered execution evidence from Python.
Do not restart the analysis from scratch.
Only call tools again if you need one missing detail for the final answer.
Prefer producing the final response now, including:
- non-trivial findings
- anomalies or outliers
- trends or patterns
- actionable recommendations
- chart filenames if any were saved
"""
            else:
                dataset_hint = f"""
A dataset has been uploaded by the user.
It is available in the session sandbox directory as: {state['dataset_filename']}
Its full path for Python code is: {session_dir}/{state['dataset_filename']}
MANDATORY RULES when a dataset is present:
1. You MUST use the Python REPL tool to inspect and analyse the data before answering.
2. Always start with:
   import pandas as pd
   import matplotlib.pyplot as plt
   df = pd.read_csv(r'{session_dir}/{state["dataset_filename"]}')
   numeric_df = df.select_dtypes(include='number')
   print(df.shape)
   print(df.dtypes)
   print(df.describe(include='all'))
   print(numeric_df.corr(numeric_only=True))
3. Your analysis MUST cover:
   - Basic statistics (already done above)
   - Correlation analysis on numeric columns only
   - Outlier / anomaly detection (IQR method or z-score)
   - At least one trend or pattern observation
   - A concrete, actionable recommendation
4. For chart generation, use matplotlib and save to {session_dir}/chart_<name>.png,
   then tell the user the filename.
5. Always print the outputs you rely on. Bare expressions are not enough in Python REPL.
6. Never call plt.show(). Save the figure and then call plt.close().
"""
        system_message = f"""You are an expert data analyst AI assistant.
You have access to a Python REPL, file tools, optional web search, and Wikipedia.
The current date and time is {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
The current session sandbox directory is: {session_dir}
{dataset_hint}
Your success criteria:
{state["success_criteria"]}
When you have finished your analysis, present:
1. A clear summary of key findings (bullet points)
2. Any anomalies or outliers found
3. Trends or patterns
4. Actionable recommendations
5. Names of any chart files saved
If you need clarification, state: "Question: <your question>"
"""
        if python_already_used:
            system_message += """
You have already used Python in this run.
Unless a crucial fact is still missing, stop calling tools and deliver the final answer.
Treat the recorded Python tool outputs as authoritative evidence; summarize them clearly in the final answer.
"""
        if state.get("feedback_on_work"):
            system_message += f"""
A previous attempt was rejected. Feedback:
{state['feedback_on_work']}
Address this feedback and improve your analysis.
"""
        # Build a new message list with an updated system message
        # (avoid mutating shared state objects in-place).
        new_messages: list = []
        sys_replaced = False
        for msg in state["messages"]:
            if isinstance(msg, SystemMessage) and not sys_replaced:
                new_messages.append(SystemMessage(content=system_message))
                sys_replaced = True
            else:
                new_messages.append(msg)
        if not sys_replaced:
            new_messages.insert(0, SystemMessage(content=system_message))
        try:
            response = self.worker_llm_with_tools.invoke(new_messages)
        except Exception as exc:
            logger.error("Worker LLM call failed: %s", exc, exc_info=True)
            return {
                "messages": [AIMessage(content=f"An error occurred during analysis: {exc}")],
                "worker_turn_count": next_worker_turn,
            }
        tool_calls = [
            tool_call.get("name", "unknown_tool")
            for tool_call in getattr(response, "tool_calls", []) or []
        ]
        return {
            "messages": [response],
            "worker_turn_count": next_worker_turn,
            "tool_calls_made": state.get("tool_calls_made", []) + tool_calls,
        }
    def worker_router(self, state: State) -> str:
        last = state["messages"][-1]
        if hasattr(last, "tool_calls") and last.tool_calls:
            return "tools"
        return "evaluator"
 
    def _format_conversation(self, messages: List[Any]) -> str:
        out = "Conversation history:\n\n"
        for msg in messages:
            if isinstance(msg, HumanMessage):
                out += f"User: {self._message_text(msg.content)}\n"
            elif isinstance(msg, AIMessage):
                text = self._message_text(msg.content) or "[Tool use]"
                out += f"Analyst: {text}\n"
            elif isinstance(msg, ToolMessage):
                out += f"Tool result ({msg.name or 'tool'}): {self._message_text(msg.content)}\n"
        return out
    def _message_text(self, content: Any) -> str:
        return normalize_message_text(content)
    def _tool_evidence(self, state: State) -> str:
        tool_calls = state.get("tool_calls_made", [])
        tool_outputs = state.get("tool_outputs_observed", [])
        dataset_present = bool(state.get("dataset_filename"))
        python_called = any(self._is_python_tool(tool) for tool in tool_calls)
        python_output_seen = any(self._is_python_tool(tool) for tool in tool_outputs)
        return (
            f"Dataset provided: {dataset_present}\n"
            f"Tool calls made: {tool_calls or ['none']}\n"
            f"Tool outputs observed: {tool_outputs or ['none']}\n"
            f"Python tool called: {python_called}\n"
            f"Python output observed: {python_output_seen}\n"
        )
    def _parse_evaluator_output(self, content: Any) -> EvaluatorOutput:
        if isinstance(content, list):
            normalized_parts = []
            for item in content:
                if isinstance(item, dict):
                    normalized_parts.append(item.get("text", str(item)))
                else:
                    normalized_parts.append(str(item))
            content = "\n".join(normalized_parts)
        elif content is None:
            content = ""
        else:
            content = str(content)
        try:
            return EvaluatorOutput.model_validate_json(content)
        except Exception:
            pass
        # Try each '{' position to find a valid JSON object.
        for i, ch in enumerate(content):
            if ch == "{":
                try:
                    obj = json.loads(content[i:])
                    return EvaluatorOutput.model_validate(obj)
                except (json.JSONDecodeError, Exception):
                    continue
        fallback_feedback = content.strip() or "Evaluator response could not be parsed."
        lower_content = fallback_feedback.lower()
        return EvaluatorOutput(
            feedback=fallback_feedback,
            success_criteria_met="meets the success criteria" in lower_content,
            user_input_needed="user input" in lower_content or "clarification" in lower_content,
            insights_are_non_trivial="non-trivial" in lower_content or "correlation" in lower_content,
        )
    def evaluator(self, state: State) -> Dict[str, Any]:
        last_response = self._message_text(state["messages"][-1].content)
        current_iteration = state.get("iteration_count", 0) + 1
        system_message = (
            "You are a senior data analyst evaluating whether a junior analyst's "
            "response to a data task meets the required standard. Be rigorous: "
            "reject responses that are only descriptive stats with no deeper insight."
        )
        user_message = f"""Evaluate this data analysis conversation.
{self._format_conversation(state["messages"])}
Execution evidence:
{self._tool_evidence(state)}
Success criteria: {state["success_criteria"]}
Final response from the analyst:
{last_response}
Evaluate:
1. Does it meet the success criteria?
2. Are insights non-trivial (correlations, anomalies, trends, recommendations)?
3. Does the analyst need user input or appear stuck?
4. Was Python actually used to derive the insights (not just described)?
If a dataset was provided, the analyst MUST have used the Python tool.
If charts were requested, at least one must have been saved.
Give the analyst reasonable benefit of the doubt on file saves.
"""
        if state.get("feedback_on_work"):
            user_message += (
                f"\nPrior feedback given: {state['feedback_on_work']}\n"
                "If the analyst is repeating the same mistakes, mark user_input_needed=True."
            )
        try:
            result_message = self.evaluator_llm.invoke([
                SystemMessage(content=system_message),
                HumanMessage(
                    content=(
                        user_message
                        + "\n\nRespond with a single JSON object only using this schema: "
                        '{"feedback": string, "success_criteria_met": boolean, '
                        '"user_input_needed": boolean, "insights_are_non_trivial": boolean}'
                    )
                ),
            ])
            result = self._parse_evaluator_output(result_message.content)
        except Exception as exc:
            logger.error("Evaluator LLM call failed: %s", exc, exc_info=True)
            result = EvaluatorOutput(
                feedback=f"Evaluator error: {exc}",
                success_criteria_met=False,
                user_input_needed=True,
                insights_are_non_trivial=False,
            )
        python_called = any(self._is_python_tool(tool) for tool in state.get("tool_calls_made", []))
        python_output_seen = any(self._is_python_tool(tool) for tool in state.get("tool_outputs_observed", []))
        # Trust actual tool evidence over the evaluator's uncertainty about whether Python was really used.
        criteria_met = (
            result.insights_are_non_trivial
            and (result.success_criteria_met or (python_called and python_output_seen and not result.user_input_needed))
        )
        hit_iteration_limit = current_iteration >= state["max_iterations"] and not criteria_met
        final_feedback = result.feedback
        user_input_needed = result.user_input_needed
        if hit_iteration_limit:
            final_feedback = (
                f"{result.feedback}\n\nMaximum retry limit reached after "
                f"{current_iteration} evaluation attempts."
            )
            user_input_needed = True
        return {
            "messages": [{
                "role": "assistant",
                "content": (
                    f"**Evaluator feedback:** {final_feedback}\n\n"
                    f"Insights non-trivial: {result.insights_are_non_trivial}"
                ),
            }],
            "feedback_on_work": final_feedback,
            "success_criteria_met": criteria_met,
            "user_input_needed": user_input_needed,
            "iteration_count": current_iteration,
        }
    def route_based_on_evaluation(self, state: State) -> str:
        if state["success_criteria_met"] or state["user_input_needed"]:
            return "END"
        return "worker"
   
    def tools_node(self, state: State) -> Dict[str, Any]:
        tool_node = self._tool_node
        result = tool_node.invoke(state)
        tool_outputs = state.get("tool_outputs_observed", []) + self._extract_tool_outputs(result["messages"])
        return {
            "messages": result["messages"],
            "tool_outputs_observed": tool_outputs,
        }
    def build_graph(self):
        builder = StateGraph(State)
        builder.add_node("worker", self.worker)
        self._tool_node = ToolNode(tools=self.tools)
        builder.add_node("tools", self.tools_node)
        builder.add_node("evaluator", self.evaluator)
        builder.add_edge(START, "worker")
        builder.add_conditional_edges(
            "worker",
            self.worker_router,
            {"tools": "tools", "evaluator": "evaluator"},
        )
        builder.add_edge("tools", "worker")
        builder.add_conditional_edges(
            "evaluator",
            self.route_based_on_evaluation,
            {"worker": "worker", "END": END},
        )
        self.graph = builder.compile(checkpointer=self.memory)
    def _extract_tool_outputs(self, messages: List[Any]) -> List[str]:
        outputs: List[str] = []
        for msg in messages:
            if isinstance(msg, ToolMessage):
                outputs.append(msg.name or "unknown_tool")
        return outputs
    
    def run(self, message: str, success_criteria: str, dataset_filename: Optional[str], history: list) -> tuple:
        config = {
            "configurable": {"thread_id": self.agent_id},
            "recursion_limit": max(50, self.max_worker_turns * 4),
        }
        state = {
            "messages": message,
            "success_criteria": success_criteria or "Provide clear, non-trivial insights from the data.",
            "dataset_filename": dataset_filename,
            "session_dir": self.session_dir,
            "feedback_on_work": None,
            "success_criteria_met": False,
            "user_input_needed": False,
            "max_iterations": self.max_iterations,
            "iteration_count": 0,
            "max_worker_turns": self.max_worker_turns,
            "worker_turn_count": 0,
            "tool_calls_made": [],
            "tool_outputs_observed": [],
        }
        result = self.graph.invoke(state, config=config)
        msgs = result["messages"]
        user_msg = {"role": "user", "content": message}
        # Guard against short message lists.
        if len(msgs) >= 2:
            analyst_reply = {"role": "assistant", "content": self._message_text(msgs[-2].content)}
            eval_feedback_text = self._message_text(msgs[-1].content)
        elif msgs:
            analyst_reply = {"role": "assistant", "content": self._message_text(msgs[-1].content)}
            eval_feedback_text = ""
        else:
            analyst_reply = {"role": "assistant", "content": "No response was generated."}
            eval_feedback_text = ""
        # Recover any chart PNGs that the agent saved to the CWD instead
        # of the session sandbox (PythonREPLTool runs in the process CWD).
        recover_orphaned_charts(self.session_dir)
        # Build notebook + HTML report for in-browser preview.
        analyst_text = analyst_reply["content"]
        code_snippets = extract_python_snippets(msgs)
        nb_path = build_notebook(
            self.session_dir, analyst_text, code_snippets, dataset_filename,
        )
        html_report = build_html_report(
            self.session_dir, analyst_text, dataset_filename,
        )
        return (
            history + [user_msg, analyst_reply],
            eval_feedback_text,
            result,
            nb_path,
            html_report,
        )
    def reset(self):
        """Return a fresh agent instance."""
        new_agent = DataAnalystAgent(
            max_iterations=self.max_iterations,
            max_worker_turns=self.max_worker_turns,
        )
        new_agent.setup()
        return new_agent
