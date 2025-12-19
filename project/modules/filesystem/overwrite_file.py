from pydantic import BaseModel, Field
import os

class OverwriteFileInput(BaseModel):
    """Input model for overwriting a file."""
    path: str = Field(..., description="The absolute path of the file to overwrite.")
    content: str = Field(..., description="The new content for the file.")

class OverwriteFileOutput(BaseModel):
    """Output model for overwriting a file."""
    status: str
    message: str

def execute(input_data: OverwriteFileInput) -> OverwriteFileOutput:
    """
    Overwrites an existing file with the specified content.

    Args:
        input_data: An object containing the path and new content for the file.

    Returns:
        An object confirming the status of the file overwrite operation.
    """
    try:
        with open(input_data.path, "w", encoding="utf-8") as f:
            f.write(input_data.content)
        return OverwriteFileOutput(status="success", message=f"File '{input_data.path}' overwritten successfully.")
    except Exception as e:
        return OverwriteFileOutput(status="error", message=f"Failed to overwrite file: {e}")
