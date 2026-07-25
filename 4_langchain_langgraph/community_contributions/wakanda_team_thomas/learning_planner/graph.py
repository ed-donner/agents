"""
Graph construction and compilation for the Learning Path Generator.
"""

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from state import State
from nodes.researcher import ResearcherNode
from nodes.curriculum_builder import CurriculumBuilderNode
from nodes.evaluator import EvaluatorNode
from nodes.markdown_writer import MarkdownWriterNode
from nodes.pdf_writer import PDFWriterNode
from nodes.notifier import NotifierNode

# Node names
NODE_RESEARCHER = "researcher"
NODE_CURRICULUM_BUILDER = "curriculum_builder"
NODE_EVALUATOR = "evaluator"
NODE_MARKDOWN_WRITER = "markdown_writer"
NODE_PDF_WRITER = "pdf_writer"
NODE_NOTIFIER = "notifier"

# Route names
ROUTE_REVISION = "revision"
ROUTE_APPROVED = "approved"

# Defaults
DEFAULT_MODEL = "gpt-4o-mini"
DEFAULT_THREAD_ID = "default"


class LearningPlannerGraph:
    """
    LangGraph-based Learning Path Generator.
    """
    
    def __init__(self, model: str = DEFAULT_MODEL):
        self.model = model
        self.graph = None
        self.memory = MemorySaver()
        self._build_graph()
    
    def _build_graph(self):
        """Build and compile the LangGraph."""
        
        # Initialize nodes
        researcher = ResearcherNode(model=self.model)
        curriculum_builder = CurriculumBuilderNode(model=self.model)
        evaluator = EvaluatorNode(model=self.model)
        markdown_writer = MarkdownWriterNode()
        pdf_writer = PDFWriterNode()
        notifier = NotifierNode()
        
        # Create graph builder
        builder = StateGraph(State)
        
        # Add nodes
        builder.add_node(NODE_RESEARCHER, researcher.execute)
        builder.add_node(NODE_CURRICULUM_BUILDER, curriculum_builder.execute)
        builder.add_node(NODE_EVALUATOR, evaluator.execute)
        builder.add_node(NODE_MARKDOWN_WRITER, markdown_writer.execute)
        builder.add_node(NODE_PDF_WRITER, pdf_writer.execute)
        builder.add_node(NODE_NOTIFIER, notifier.execute)
        
        builder.add_edge(START, NODE_RESEARCHER)
        builder.add_edge(NODE_RESEARCHER, NODE_CURRICULUM_BUILDER)
        builder.add_edge(NODE_CURRICULUM_BUILDER, NODE_EVALUATOR)

        builder.add_conditional_edges(
            NODE_EVALUATOR,
            self._route_after_evaluation,
            {
                ROUTE_REVISION: NODE_CURRICULUM_BUILDER,
                ROUTE_APPROVED: NODE_MARKDOWN_WRITER,
            }
        )
        builder.add_edge(NODE_MARKDOWN_WRITER, NODE_PDF_WRITER)
        builder.add_edge(NODE_PDF_WRITER, NODE_NOTIFIER)
        builder.add_edge(NODE_NOTIFIER, END)
        self.graph = builder.compile(checkpointer=self.memory)
    
    def _route_after_evaluation(self, state: State) -> str:
        """Route based on evaluation result."""
        if state.get("is_complete", False):
            return ROUTE_APPROVED
        
        if state.get("needs_user_input", False):
            return ROUTE_APPROVED
        
        return ROUTE_REVISION
    
    def run(self, topic: str, skill_level: str, time_commitment: str, 
            user_email: str = "", thread_id: str = DEFAULT_THREAD_ID) -> State:
        """Run the learning path generator."""
        
        initial_state = {
            "topic": topic,
            "current_skill_level": skill_level,
            "time_commitment": time_commitment,
            "user_email": user_email,
            "messages": [],
            "prerequisites": None,
            "key_concepts": None,
            "research_summary": None,
            "curriculum": None,
            "evaluation_feedback": None,
            "is_complete": False,
            "needs_user_input": False,
            "revision_count": 0,
            "markdown_content": None,
            "markdown_path": None,
            "pdf_path": None,
            "notification_status": None,
            "notification_sent": False,
        }
        
        config = {"configurable": {"thread_id": thread_id}}
        result = self.graph.invoke(initial_state, config=config)
        return result
    
    def get_graph_image(self):
        """Get the graph visualization as PNG bytes."""
        return self.graph.get_graph().draw_mermaid_png()
