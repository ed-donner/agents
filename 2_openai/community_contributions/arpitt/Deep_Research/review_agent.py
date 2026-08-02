from typing import List

from dotenv import load_dotenv
from agents import Agent, ModelSettings
from pydantic import BaseModel, Field

load_dotenv(override=True)

INSTRUCTIONS="""YOu are a review agent. Yu will receive a deep research created by another agents,
on a topic given by the user. Your job is to go through the report carefully and review it,
and finally, give the generated report rating out of 10 and small 4 bullets points of what could have been better """

class review(BaseModel):
    score : float = Field(description = 'The score of the report out of 10')

    feedback : str = Field(description='feedback of the report')

review_agent = Agent(name='review_agent',
                     instructions=INSTRUCTIONS,
                     model ='gpt-4o-mini',
                     output_type=review)

