from autogen_agentchat.agents import AssistantAgent
from autogen_ext.models.openai import OpenAIChatCompletionClient
from config import get_model_client

model_client = get_model_client()


def create_goal_analyzer():
    return AssistantAgent(
        name="goal_analyzer",
        model_client=model_client,
        system_message="""
You are a goal analyzer.

Convert user goals into actionable tasks.

Rules:
- Be specific
- Break down big goals
- Output as bullet points only
"""
    )


def create_scheduler():
    return AssistantAgent(
        name="scheduler",
        model_client=model_client,
        system_message="""
Create a daily schedule from tasks.

Rules:
- Assign realistic time blocks
- Include breaks
- Format:

Time - Task
"""
    )


def create_optimizer():
    return AssistantAgent(
        name="optimizer",
        model_client=model_client,
        system_message="""
Improve the schedule:

- Put hardest tasks first
- Add short motivational tips
- Ensure balance

Return final schedule only.
"""
    )