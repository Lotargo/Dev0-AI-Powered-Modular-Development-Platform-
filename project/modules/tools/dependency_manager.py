"""
Dependency Manager Module.
Allows agents to add Python packages to the project using Poetry.
"""
import subprocess
from pydantic import BaseModel, Field
from project.core.framework.atomic import atomic

class AddDependencyInput(BaseModel):
    package_name: str = Field(..., description="The name of the package to install (e.g. 'requests', 'numpy').")
    is_dev: bool = Field(False, description="Whether to install as a development dependency.")

class AddDependencyOutput(BaseModel):
    success: bool = Field(..., description="Whether the installation was successful.")
    message: str = Field(..., description="Output log or error message.")

@atomic
def execute(input_data: AddDependencyInput) -> AddDependencyOutput:
    """
    Adds a dependency to the project using 'poetry add'.
    """
    cmd = ["poetry", "add"]
    if input_data.is_dev:
        cmd.append("--group")
        cmd.append("dev")

    cmd.append(input_data.package_name)

    try:
        # Run with capture_output to get logs
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False
        )

        if result.returncode == 0:
            return AddDependencyOutput(success=True, message=f"Successfully installed {input_data.package_name}.\n{result.stdout}")
        else:
            return AddDependencyOutput(success=False, message=f"Failed to install {input_data.package_name}.\nStderr: {result.stderr}\nStdout: {result.stdout}")

    except Exception as e:
        return AddDependencyOutput(success=False, message=f"Exception during dependency installation: {str(e)}")
