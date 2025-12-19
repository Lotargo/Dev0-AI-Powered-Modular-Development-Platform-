from pydantic import BaseModel
from typing import Type, Dict, Any

def pydantic_to_json_schema(model: Type[BaseModel], function_name: str, function_description: str) -> Dict[str, Any]:
    """
    Converts a Pydantic model to a JSON Schema dictionary formatted for LLM function calling.

    Args:
        model: The Pydantic model class to convert.
        function_name: The name of the function the LLM should call.
        function_description: A description of what the function does.

    Returns:
        A dictionary representing the JSON Schema for the tool.
    """
    schema = model.model_json_schema()

    # We only need the properties and required fields from the schema
    parameters = {
        "type": "object",
        "properties": schema.get("properties", {}),
    }
    required = schema.get("required")
    if required:
        parameters["required"] = required

    return {
        "type": "function",
        "function": {
            "name": function_name,
            "description": function_description,
            "parameters": parameters,
        },
    }
