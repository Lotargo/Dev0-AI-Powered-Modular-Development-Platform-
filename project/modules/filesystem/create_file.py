"""This module provides a function to create a new file with content.
It takes a path and content as input, and writes the content to the file
at the specified path.
"""
from pydantic import BaseModel, Field


class CreateFileInput(BaseModel):
    """Input model for the create_file function.
    Attributes:
        path: The path of the file to create.
        content: The content to write to the file.
    """
    path: str = Field(..., description="The path of the file to create.")
    content: str = Field(..., description="The content to write to the file.")


class CreateFileOutput(BaseModel):
    """Output model for the create_file function.
    Attributes:
        message: The result of the operation.
    """
    message: str = Field(..., description="The result of the operation.")


from project.core.framework.atomic import atomic

@atomic
def execute(input_data: CreateFileInput) -> CreateFileOutput:
    """Creates a new file with content at the specified path.
    Args:
        input_data: A CreateFileInput object containing the path and content.
    Returns:
        A CreateFileOutput object with a message indicating the result.
    """
    try:
        with open(input_data.path, 'w', encoding='utf-8') as f:
            f.write(input_data.content)
        return CreateFileOutput(message=f"File '{input_data.path}' created successfully.")
    except Exception as e:
        return CreateFileOutput(message=f"An unexpected error occurred: {e}")
