"""
A test module that simulates a long-running, blocking I/O operation.
"""
import time
from pydantic import BaseModel, Field
from project.core.framework.atomic import atomic
from project.core.framework.concurrent import concurrent

class Input(BaseModel):
    duration: float = Field(default=2.0, description="The duration to sleep in seconds.")

class Output(BaseModel):
    message: str

@atomic
@concurrent
def execute(input_data: Input) -> Output:
    """
    Simulates a blocking I/O operation by sleeping for a specified duration
    and then returns a success message.
    """
    print(f"Long sleep module started, sleeping for {input_data.duration} seconds in a thread...")
    time.sleep(input_data.duration)
    print("Long sleep module finished.")
    return Output(message=f"Slept for {input_data.duration} seconds.")
