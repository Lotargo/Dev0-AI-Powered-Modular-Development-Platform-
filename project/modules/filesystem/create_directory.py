"""This module provides a function to create a new directory.
It takes a path as input and creates the directory at that path.
"""
import os
from pydantic import BaseModel, Field


class CreateDirectoryInput(BaseModel):
    """Input model for the create_directory function.
    Attributes:
        path: The path of the directory to create.
    """
    path: str = Field(..., description="The path of the directory to create.")


class CreateDirectoryOutput(BaseModel):
    """Output model for the create_directory function.
    Attributes:
        message: The result of the operation.
    """
    message: str = Field(..., description="The result of the operation.")


from project.core.framework.atomic import atomic

@atomic
def execute(input_data: CreateDirectoryInput) -> CreateDirectoryOutput:
    """Creates a new directory at the specified path.
    Args:
        input_data: A CreateDirectoryInput object containing the path.
    Returns:
        A CreateDirectoryOutput object with a message indicating the result.
    """
    try:
        os.makedirs(input_data.path, exist_ok=True)
        return CreateDirectoryOutput(message=f"Directory '{input_data.path}' created successfully.")
    except Exception as e:
        return CreateDirectoryOutput(message=f"An unexpected error occurred: {e}")
