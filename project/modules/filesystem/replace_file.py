from pydantic import BaseModel, Field
import os
import shutil

class ReplaceFileInput(BaseModel):
    """Input model for replacing a file."""
    source_path: str = Field(..., description="The absolute path of the source file.")
    destination_path: str = Field(..., description="The absolute path of the destination file to be replaced.")

class ReplaceFileOutput(BaseModel):
    """Output model for replacing a file."""
    status: str
    message: str

def execute(input_data: ReplaceFileInput) -> ReplaceFileOutput:
    """
    Replaces a destination file with a source file.

    Args:
        input_data: An object containing the source and destination paths.

    Returns:
        An object confirming the status of the file replacement operation.
    """
    try:
        shutil.copy2(input_data.source_path, input_data.destination_path)
        return ReplaceFileOutput(status="success", message=f"File '{input_data.destination_path}' replaced successfully with '{input_data.source_path}'.")
    except Exception as e:
        return ReplaceFileOutput(status="error", message=f"Failed to replace file: {e}")
