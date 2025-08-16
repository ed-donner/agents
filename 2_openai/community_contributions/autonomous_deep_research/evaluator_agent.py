from pydantic import BaseModel, Field
from agents import Agent, Runner, OpenAIChatCompletionsModel
from openai import AsyncOpenAI

import os


INSTRUCTION = f"""You are an evaluator which decides a research report for the topic is acceptable. You are provided a research report and a topic. 
Your task is to decide is report is well written, conscise and easy to follow for a non technical person."""

google_api_key = os.getenv('GOOGLE_API_KEY')
if not google_api_key:
    raise Exception("GOOGLE_API_KEY is not set")

GEMINI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai/"
gemini_client = AsyncOpenAI(base_url=GEMINI_BASE_URL, api_key=google_api_key)
gemini_model = OpenAIChatCompletionsModel(model="gemini-2.0-flash", openai_client=gemini_client)


class Evaluation(BaseModel):
    is_acceptable: bool
    feedback: str

eval_agent = Agent(
    name = "Evaluator Agent",
    instructions=INSTRUCTION,
    model = gemini_model,
    output_type = Evaluation,
)

async def evaluate(topic: str, report: str) -> Evaluation:
    """
    Evaluates if the report is according to the standards
    """
    user_prompt = "Here is the research topic and generated report"
    user_prompt += f"\n\nTopic: {topic}\n\n"
    user_prompt += f"\n\nReport: {report}\n\n"
    user_prompt += "Please evaluate the report, replying with whether it is acceptable with your feedback"

    result = await Runner.run(eval_agent, user_prompt)
    print ("Evaluation result: ", result)
    return result.final_output_as(Evaluation)

eval_agent_tool = eval_agent.as_tool(tool_name="eval_tool", tool_description="Evaluates if the research report is according to the standards or not")
