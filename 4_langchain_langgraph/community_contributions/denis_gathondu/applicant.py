import uuid
from typing import Any, Dict, List

from applicant_agents import ApplicantAgent
from dotenv import load_dotenv
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import START, StateGraph
from models import EvaluationList, JobPostingList, NotificationList, State

load_dotenv(override=True)


class Applicant:
    def __init__(
        self,
        username: str,
        no_of_postings: int,
        model: str,
    ):
        self.graph = None
        self.applicant_id = str(uuid.uuid4())
        self.memory = MemorySaver()
        self.agent = None
        self.username = username
        self.no_of_postings = no_of_postings
        self.model = model

    async def setup(self):
        self.agent = ApplicantAgent(
            username=self.username,
            no_of_postings=self.no_of_postings,
            model=self.model,
        )
        await self.agent.setup()
        await self.build_graph()

    async def build_graph(self):
        # Set up Graph Builder with State
        graph_builder = StateGraph(State)

        # Add nodes
        graph_builder.add_node("listing_worker", self.agent.listing_worker)
        graph_builder.add_node(
            "evaluate_job_postings", self.agent.evaluate_job_postings
        )
        graph_builder.add_node("notification_worker", self.agent.notification_worker)
        graph_builder.add_node(
            "notification_response", self.agent.notification_response
        )

        # Add edges
        graph_builder.add_edge("listing_worker", "evaluate_job_postings")
        graph_builder.add_edge("evaluate_job_postings", "notification_worker")
        graph_builder.add_edge("notification_worker", "notification_response")
        graph_builder.add_edge(START, "listing_worker")

        # Compile the graph
        self.graph = graph_builder.compile(checkpointer=self.memory)

    async def run_superstep(
        self, message: str, job_posting_url: str, history: List[Dict[str, Any]]
    ):
        config = {"configurable": {"thread_id": self.applicant_id}}

        state = {
            "messages": message,
            "job_posting_url": job_posting_url,
            "job_postings": JobPostingList(job_postings=[]),
            "evaluations": EvaluationList(evaluations=[]),
            "notifications": NotificationList(notifications=[]),
        }
        result = await self.graph.ainvoke(state, config=config)
        user = {"role": "user", "content": message}
        reply = {"role": "assistant", "content": result["messages"][-1].content}
        return history + [user, reply]

    def cleanup(self):
        self.agent.cleanup()
