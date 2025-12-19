from pydantic import BaseModel, Field
from typing import Dict, Any

class ModuleV1(BaseModel):
    """
    Represents the contract for a version 1 module.
    """
    name: str = Field(..., description="The unique name of the module.")
    description: str = Field(..., description="A brief description of what the module does.")
    category: str = Field(..., description="The category the module belongs to.")

    input_schema: Dict[str, Any] = Field(..., description="The JSON schema for the input model.")
    output_schema: Dict[str, Any] = Field(..., description="The JSON schema for the output model.")
