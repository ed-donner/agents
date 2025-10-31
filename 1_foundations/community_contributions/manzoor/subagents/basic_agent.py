from pydantic import BaseModel

class BasicAgent(BaseModel):
    """ A simple sub-agent"""
    name:str
    description:str
    model:str

    
    