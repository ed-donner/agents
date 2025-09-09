import queue
from typing import Any

from pydantic import BaseModel, Field

class TaskInfo(BaseModel):
    name: str = Field(description="Name of the task")
    type: str = Field(description="Task type. Could be markdown or code")
    output: Any = Field(description="Task output. could be any object")


# shared task output queue. this is a singleton apparently :-).
shared_task_output_queue: "queue.Queue[TaskInfo]" = queue.Queue()

def add_to_queue(taskInfo : TaskInfo):
    shared_task_output_queue.put(taskInfo)
