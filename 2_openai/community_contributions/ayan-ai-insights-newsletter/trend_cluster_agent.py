from dotenv import load_dotenv
from agents import Agent
from pydantic import BaseModel, Field
from typing import List
from datetime import datetime

load_dotenv(override=True)

class TrendCluster(BaseModel):
    cluster_name: str = Field(description="The name of the cluster")
    cluster_summary: str = Field(description="A summary of the cluster")
    item_titles: List[str] = Field(description="The titles of the items in the cluster")

class TrendClusterOutput(BaseModel):
    clusters: List[TrendCluster] = Field(description="The clusters of the newsletter")

with open("system_prompts/trend_cluster_agent_prompt.txt", "r") as f:
    trend_cluster_prompt = f"Today's date is {datetime.now().strftime('%Y-%m-%d')}. "
    trend_cluster_prompt += f.read()

trend_cluster_agent = Agent(
    name="Trend Cluster Agent",
    instructions=trend_cluster_prompt,
    model="gpt-4o-mini",
    output_type=TrendClusterOutput
)