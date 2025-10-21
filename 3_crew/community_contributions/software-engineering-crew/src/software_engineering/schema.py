from pydantic import BaseModel, Field, constr
from typing import Literal, Optional


class ModuleSpec(BaseModel):
    name: constr(pattern=r'.+\.py$')      # must end with .py
    class_name: constr(pattern=r'^[A-Z][A-Za-z0-9_]*$')  # valid class name
    purpose: str = Field(description='The purpose of the module')


class ProjectSpec(BaseModel):
    modules: list[ModuleSpec]
