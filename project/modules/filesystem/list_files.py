"""This module provides a function to list files and directories in a given path.
"""
from pydantic import BaseModel, Field
from typing import List
from pathlib import Path


class ListFilesInput(BaseModel):
    """Input model for the list_files function.
    Attributes:
        path: The path of the directory to list.
    """
    path: str = Field(..., description="The path of the directory to list.")


class ListFilesOutput(BaseModel):
    """Output model for the list_files function.
    Attributes:
        files: A list of files and directories.
        error: An error message if the operation failed.
    """
    files: List[str] = Field(None, description="The list of files and directories.")
    error: str = Field(None, description="An error message if the operation failed.")


def execute(input_data: ListFilesInput) -> ListFilesOutput:
    """Lists the files and directories at the specified path.
    Args:
        input_data: A ListFilesInput object containing the path to list.
    Returns:
        A ListFilesOutput object with the list of files and directories,
        or an error message if the operation failed.
    """
    try:
        path = Path(input_data.path)
        if not path.is_dir():
            return ListFilesOutput(error=f"Error: Path '{input_data.path}' is not a directory.")

        items = [item.name for item in path.iterdir()]
        return ListFilesOutput(files=items)
    except Exception as e:
        return ListFilesOutput(error=f"An unexpected error occurred: {e}")
