from pydantic import BaseModel

class DummyModuleInput(BaseModel):
    value: int

class DummyModuleOutput(BaseModel):
    result: int

def execute(input_data: DummyModuleInput) -> DummyModuleOutput:
    """A dummy module that doubles an integer."""
    return DummyModuleOutput(result=input_data.value * 2)
