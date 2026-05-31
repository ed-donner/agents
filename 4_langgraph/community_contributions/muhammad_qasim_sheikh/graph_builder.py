from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from state import ResearchState
from nodes.clarifier_node import clarifier_node
from nodes.topic_generator_node import topic_generator_node
from nodes.topic_evaluator_node import topic_evaluator_node
from nodes.summarizer_node import summarizer_agent_node
from nodes.report_writer_node import report_writer_node
from nodes.report_evaluator_node import report_evaluator_node
from nodes.file_writer_node import file_writer_node
from nodes.html_convertor_node import html_converter_node
from nodes.email_node import email_node
from nodes.push_notification_node import push_notification_node

def route_after_evaluation(state: ResearchState) -> str:
    print("CHECKING: Topic Evaluation")
    print(state.retry_count)
    if state.is_acceptable:
        return "run_research"
    
    if state.retry_count >= 3:
        print("Max retries reached. Using best topics.")
        state.topics = state.best_topics
        return "run_research"
    else:
        print(f"Retrying")
        return "retry"

def route_after_report_eval(state: ResearchState) -> str:
    print("CHECKING: Report Evaluation")
    print(state.report_retry_count)
    if state.report_is_acceptable:
        return "save_report_file"
    
    if state.report_retry_count >= 3:
        print("Max report retries reached. Using best version available.")
        state.report = state.best_report
        state.report_score = state.best_report_score
        state.report_feedback = state.best_report_feedback
        return "save_report_file"
    else:
        print(f"Retrying Report Generation")
        return "retry"

def build_graph():
    graph_builder = StateGraph(ResearchState)
    graph_builder.add_node("clarifier", clarifier_node)
    graph_builder.add_node("topic_generator", topic_generator_node)
    graph_builder.add_node("topic_evaluator", topic_evaluator_node)
    graph_builder.add_node("summarizer_agent", summarizer_agent_node)
    graph_builder.add_node("report_writer", report_writer_node)
    graph_builder.add_node("report_evaluator", report_evaluator_node)
    graph_builder.add_node("file_writer", file_writer_node)
    graph_builder.add_node("html_converter", html_converter_node)
    graph_builder.add_node("email", email_node)
    graph_builder.add_node("push_notification", push_notification_node)

    graph_builder.add_edge(START, "clarifier")
    graph_builder.add_edge("clarifier", "topic_generator")
    graph_builder.add_edge("topic_generator", "topic_evaluator")

    graph_builder.add_conditional_edges(
        "topic_evaluator",
        route_after_evaluation,
        {
         "retry": "topic_generator",
         "run_research": "summarizer_agent"
        }
    )

    graph_builder.add_edge("summarizer_agent", "report_writer")
    graph_builder.add_edge("report_writer", "report_evaluator")

    graph_builder.add_conditional_edges(
        "report_evaluator",
        route_after_report_eval,
        {
         "retry": "report_writer",
         "save_report_file": "file_writer"
        }
    )
    graph_builder.add_edge("file_writer", "html_converter")
    graph_builder.add_edge("html_converter", "email")
    graph_builder.add_edge("email", "push_notification")
    graph_builder.add_edge("push_notification", END)

    checkpointer = MemorySaver()

    # Pause after clarifier so UI can collect answers
    return graph_builder.compile(checkpointer=checkpointer)

research_graph  = build_graph()