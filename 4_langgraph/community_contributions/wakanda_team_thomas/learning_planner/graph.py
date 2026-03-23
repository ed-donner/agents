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


class LearningPlannerGraph:
    """
    LangGraph-based Learning Path Generator.
    """
    
    def __init__(self, model: str = "gpt-4o-mini"):
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
        builder.add_node("researcher", researcher.execute)
        builder.add_node("curriculum_builder", curriculum_builder.execute)
        builder.add_node("evaluator", evaluator.execute)
        builder.add_node("markdown_writer", markdown_writer.execute)
        builder.add_node("pdf_writer", pdf_writer.execute)
        builder.add_node("notifier", notifier.execute)
        
        # Add edges
        builder.add_edge(START, "researcher")
        builder.add_edge("researcher", "curriculum_builder")
        builder.add_edge("curriculum_builder", "evaluator")
        
        # Conditional edge from evaluator
        builder.add_conditional_edges(
            "evaluator",
            self._route_after_evaluation,
            {
                "revision": "curriculum_builder",
                "approved": "markdown_writer",
            }
        )
        
        # Continue to writers and notifier
        builder.add_edge("markdown_writer", "pdf_writer")
        builder.add_edge("pdf_writer", "notifier")
        builder.add_edge("notifier", END)
        
        # Compile with memory
        self.graph = builder.compile(checkpointer=self.memory)
    
    def _route_after_evaluation(self, state: State) -> str:
        """Route based on evaluation result."""
        if state.get("is_complete", False):
            return "approved"
        
        if state.get("needs_user_input", False):
            return "approved"
        
        return "revision"
    
    def run(self, topic: str, skill_level: str, time_commitment: str, 
            user_email: str = "", thread_id: str = "default") -> State:
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
