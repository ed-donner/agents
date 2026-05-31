from typing import Annotated, List, Any, Optional, Dict
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.memory import MemorySaver
from langchain_openai import ChatOpenAI
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from pydantic import BaseModel, Field
from datetime import datetime
from config import LogAnalyzerConfig
from analyzer_tools import AnalyzerTools
import uuid
import asyncio
import os


class State(TypedDict):
    messages: Annotated[List[Any], add_messages]
    log_file_path: str
    analysis_criteria: str
    feedback_on_work: Optional[str]
    analysis_complete: bool
    user_input_needed: bool


class EvaluatorOutput(BaseModel):
    feedback: str = Field(description="Detailed feedback on the analysis quality and completeness")
    analysis_complete: bool = Field(description="Whether the analysis meets all criteria and is complete")
    user_input_needed: bool = Field(description="Whether user input or clarification is needed")


class LogAnalyzerAgent:
    def __init__(self, config: LogAnalyzerConfig):
        self.config = config
        self.worker_llm_with_tools = None
        self.evaluator_llm_with_output = None
        self.tools = None
        self.graph = None
        self.agent_id = str(uuid.uuid4())
        self.memory = MemorySaver()
        self.browser = None
        self.playwright = None

    async def setup(self):
        root_dir = os.path.dirname(os.path.abspath(__file__))
        self.tools, self.browser, self.playwright = await AnalyzerTools.setup_all_tools(
            root_dir,
            enable_browser=self.config.enable_browser_tools
        )

        worker_llm = ChatOpenAI(model=self.config.llm_model)
        self.worker_llm_with_tools = worker_llm.bind_tools(self.tools)

        evaluator_llm = ChatOpenAI(model=self.config.llm_model)
        self.evaluator_llm_with_output = evaluator_llm.with_structured_output(EvaluatorOutput)

        await self.build_graph()

    def worker(self, state: State) -> Dict[str, Any]:
        system_message = f"""You are a DevOps Log Analyzer assistant with access to multiple tools.
Your task is to analyze log files, investigate source code for errors, and provide actionable solutions.

Current date and time: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

Analysis Criteria: {state['analysis_criteria']}
Log File: {state['log_file_path']}

Configuration:
- Logs Directory: {self.config.logs_directory}
- Source Code Directory: {self.config.source_code_directory}
- Error Patterns: {', '.join(self.config.error_patterns)}
- Max Errors to Analyze: {self.config.max_errors_to_analyze}
- Source Investigation: {'Enabled' if self.config.enable_source_investigation else 'Disabled'}
- Notifications: {'Enabled' if self.config.enable_notifications else 'Disabled'}
- Browser Tools: {'Enabled' if self.config.enable_browser_tools else 'Disabled'}

Available Tools:
1. File Management: read_file, write_file, list_directory - Use these to read logs and source code
2. Python REPL: python_repl_ast - Use this to parse logs, extract patterns, and analyze data
3. Search: search - Search online for error solutions and best practices
4. Wikipedia: wikipedia - Look up technical concepts
{'5. Browser: navigate_browser, extract_text - Check documentation and Stack Overflow' if self.config.enable_browser_tools else ''}
{'6' if self.config.enable_browser_tools else '5'}. Notifications: send_push_notification - Send alerts for critical errors

Your workflow should be:
1. Read the log file using file tools
2. Parse and identify errors using Python REPL (look for: {', '.join(self.config.error_patterns)})
3. For each error found:
   - Extract context (timestamp, severity, message)
   - If source code file is mentioned and source investigation is enabled:
     * Search source code directory for the file
     * Read the relevant source code
     * Identify the root cause
   - Search online for solutions
4. Generate a comprehensive analysis report
5. If critical errors (FATAL) found and notifications enabled, send notification
6. Provide your final analysis

IMPORTANT - Push Notification Format:
When sending push notifications for critical errors, create a well-formatted, descriptive message that includes:
- A clear alert title/summary
- Number and types of critical errors found
- Affected components/services (file names, line numbers)
- Brief description of the root cause if identified
- Impact statement (what's broken, what's at risk)
- Recommended immediate actions

Example notification format:
```
CRITICAL: Authentication Service Failures

Found 5 FATAL errors in authentication.log:
- JWT signature validation failures (AuthService.py:89)
- Intermittent token validation errors affecting users 1042, 1043

Root Cause: Stale secret key cache in SecurityConfig.py causing signature mismatch after key rotation

Impact: Users unable to authenticate, service degradation

Action Required:
1. Invalidate secret key cache immediately
2. Restart authentication service
3. Verify JWT secret key rotation procedure
```

Keep notifications concise but informative (max 300 words). Focus on actionability.

If you have questions or need clarification, clearly state: "Question: [your question]"
Otherwise, provide your complete analysis.
"""

        if state.get("feedback_on_work"):
            system_message += f"""

Previous Attempt Feedback:
{state['feedback_on_work']}

Please address this feedback and improve your analysis. Ensure you meet all the criteria.
"""

        found_system_message = False
        messages = state["messages"]
        for message in messages:
            if isinstance(message, SystemMessage):
                message.content = system_message
                found_system_message = True
                break

        if not found_system_message:
            messages = [SystemMessage(content=system_message)] + messages

        response = self.worker_llm_with_tools.invoke(messages)
        return {"messages": [response]}

    def worker_router(self, state: State) -> str:
        last_message = state["messages"][-1]
        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            return "tools"
        return "evaluator"

    def format_conversation(self, messages: List[Any]) -> str:
        conversation = "Conversation History:\n\n"
        for message in messages:
            if isinstance(message, HumanMessage):
                conversation += f"User: {message.content}\n\n"
            elif isinstance(message, AIMessage):
                text = message.content or "[Tool execution]"
                conversation += f"Agent: {text}\n\n"
        return conversation

    def evaluator(self, state: State) -> Dict[str, Any]:
        last_response = state["messages"][-1].content

        system_message = """You are an evaluator assessing the quality and completeness of a log analysis.
Your job is to determine if the agent has successfully completed the analysis according to the criteria.

Evaluate based on:
1. Were all errors matching the criteria found and listed?
2. Is the error severity properly assessed?
3. If source investigation was enabled, was source code analyzed?
4. Are the suggested solutions relevant and actionable?
5. Is the analysis clear and well-structured?
6. If critical errors were found, was a notification sent (if enabled)?

Be strict but fair. If something is missing or unclear, provide specific feedback.
"""

        user_message = f"""Evaluate this log analysis:

{self.format_conversation(state['messages'])}

Analysis Criteria: {state['analysis_criteria']}
Log File: {state['log_file_path']}

Agent's Final Response:
{last_response}

Configuration Context:
- Source Investigation: {'Enabled' if self.config.enable_source_investigation else 'Disabled'}
- Notifications: {'Enabled' if self.config.enable_notifications else 'Disabled'}
- Error Patterns to Look For: {', '.join(self.config.error_patterns)}

Provide your evaluation:
1. Feedback: Detailed assessment of what was done well and what's missing
2. Analysis Complete: True only if all criteria are met
3. User Input Needed: True if the agent has questions or is stuck
"""

        if state.get("feedback_on_work"):
            user_message += f"""

Previous Feedback Given: {state['feedback_on_work']}

If the agent is repeating the same mistakes or not improving, set user_input_needed to True.
"""

        evaluator_messages = [
            SystemMessage(content=system_message),
            HumanMessage(content=user_message),
        ]

        eval_result = self.evaluator_llm_with_output.invoke(evaluator_messages)

        return {
            "messages": [
                {
                    "role": "assistant",
                    "content": f"Evaluator Feedback: {eval_result.feedback}",
                }
            ],
            "feedback_on_work": eval_result.feedback,
            "analysis_complete": eval_result.analysis_complete,
            "user_input_needed": eval_result.user_input_needed,
        }

    def evaluation_router(self, state: State) -> str:
        if state["analysis_complete"] or state["user_input_needed"]:
            return "END"
        return "worker"

    async def build_graph(self):
        graph_builder = StateGraph(State)

        graph_builder.add_node("worker", self.worker)
        graph_builder.add_node("tools", ToolNode(tools=self.tools))
        graph_builder.add_node("evaluator", self.evaluator)

        graph_builder.add_conditional_edges(
            "worker", self.worker_router, {"tools": "tools", "evaluator": "evaluator"}
        )

        graph_builder.add_edge("tools", "worker")

        graph_builder.add_conditional_edges(
            "evaluator", self.evaluation_router, {"worker": "worker", "END": END}
        )

        graph_builder.add_edge(START, "worker")

        self.graph = graph_builder.compile(checkpointer=self.memory)

    async def analyze_log(self, log_file_path: str, analysis_criteria: str, history: List):
        config = {"configurable": {"thread_id": self.agent_id}}

        state = {
            "messages": history if history else [],
            "log_file_path": log_file_path,
            "analysis_criteria": analysis_criteria or "Find and analyze all errors in the log file",
            "feedback_on_work": None,
            "analysis_complete": False,
            "user_input_needed": False,
        }

        result = await self.graph.ainvoke(state, config=config)

        user_msg = {"role": "user", "content": f"Analyze {log_file_path}: {analysis_criteria}"}

        agent_response = {"role": "assistant", "content": result["messages"][-2].content}

        evaluator_feedback = {"role": "assistant", "content": result["messages"][-1].content}

        return history + [user_msg, agent_response, evaluator_feedback]

    def cleanup(self):
        if self.browser:
            try:
                loop = asyncio.get_running_loop()
                loop.create_task(self.browser.close())
                if self.playwright:
                    loop.create_task(self.playwright.stop())
            except RuntimeError:
                asyncio.run(self.browser.close())
                if self.playwright:
                    asyncio.run(self.playwright.stop())

    def get_log_files(self) -> List[str]:
        logs_path = self.config.get_absolute_logs_path()
        if not os.path.exists(logs_path):
            return []

        log_files = []
        for file in os.listdir(logs_path):
            if file.endswith(('.log', '.txt')):
                log_files.append(file)

        return sorted(log_files)
