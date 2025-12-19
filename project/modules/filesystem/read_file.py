"""This module provides a function to read the content of a file.
"""
from pydantic import BaseModel, Field
from pathlib import Path


class ReadFileInput(BaseModel):
    """Input model for the read_file function.
    Attributes:
        path: The path of the file to read.
    """
    path: str = Field(..., description="The path of the file to read.")


class ReadFileOutput(BaseModel):
    """Output model for the read_file function.
    Attributes:
        content: The content of the file.
        error: An error message if the operation failed.
    """
    content: str = Field(None, description="The content of the file.")
    error: str = Field(None, description="An error message if the operation failed.")


def execute(input_data: ReadFileInput) -> ReadFileOutput:
    """Reads the content of a file at the specified path.
    Args:
        input_data: A ReadFileInput object containing the path of the file to read.
    Returns:
        A ReadFileOutput object with the content of the file, or an error
        message if the operation failed.
    """
    try:
        path = Path(input_data.path)
        if not path.is_file():
            return ReadFileOutput(error=f"Error: Path '{input_data.path}' is not a file.")

        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
        return ReadFileOutput(content=content)
    except Exception as e:
        return ReadFileOutput(error=f"An unexpected error occurred: {e}")
