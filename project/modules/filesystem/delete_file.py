"""
This module provides a secure function to delete a file from the filesystem.
It is useful for cleaning up temporary files or removing processed content.
IMPORTANT: The execute function requires a 'DeleteFileInput' model with a 'path' field.
"""
import os
from pydantic import BaseModel, Field

class DeleteFileInput(BaseModel):
    path: str = Field(..., description="The path to the file to be deleted.")

class DeleteFileOutput(BaseModel):
    status: str = Field(..., description="The status of the deletion operation.")
    message: str = Field(..., description="A message describing the result.")

from project.core.framework.atomic import atomic

@atomic
def execute(input_data: DeleteFileInput) -> DeleteFileOutput:
    """Deletes a file at the specified path."""
    try:
        if os.path.exists(input_data.path) and os.path.isfile(input_data.path):
            os.remove(input_data.path)
            return DeleteFileOutput(status="success", message=f"File '{input_data.path}' deleted.")
        elif not os.path.exists(input_data.path):
            return DeleteFileOutput(status="error", message="File not found.")
        else:
            return DeleteFileOutput(status="error", message="Path is a directory, not a file.")
    except Exception as e:
        return DeleteFileOutput(status="error", message=str(e))
