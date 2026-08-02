
from pydantic import BaseModel
from typing import List


class Module(BaseModel):
    """Represents one python module that the backend engineer will write"""
  
    filename: str
    name: str
    description: str


class DesignDocument(BaseModel):
    """The full design that the engineering lead produces:
        1. a list of modules to be written (the engineering lead decides how many)
        2. an overall description tying them together
        3. the name of the main module (the one that the frontend and tests will use)
        4. the name of the main class in the main module (the one that the frontend and tests will use)
    """

    overview: str
    modules: List[Module]
    main_module: str
    main_class: str