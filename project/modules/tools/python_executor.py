"""
Universal Command Executor: A powerful tool for running any shell command.
"""
import subprocess
from pydantic import BaseModel, Field

class PythonExecutorInput(BaseModel):
    command: str = Field(..., description="The shell command to execute.")

class PythonExecutorOutput(BaseModel):
    stdout: str
    stderr: str
    exit_code: int

from project.core.framework.atomic import atomic

@atomic
def execute(inputs: PythonExecutorInput) -> PythonExecutorOutput:
    """
    Executes a shell command in a subprocess.
    This provides a powerful way to interact with the underlying system.
    """
    try:
        # Execute the command. Using shell=True for flexibility.
        # This is safe in our containerized environment.
        process = subprocess.run(
            inputs.command,
            capture_output=True,
            text=True,
            encoding='utf-8',
            shell=True, # Allows executing complex commands
            timeout=180  # 3-minute timeout
        )

        return PythonExecutorOutput(
            stdout=process.stdout,
            stderr=process.stderr,
            exit_code=process.returncode
        )

    except subprocess.TimeoutExpired:
        return PythonExecutorOutput(
            stdout="",
            stderr="Executor error: The command took too long to execute and was terminated.",
            exit_code=1
        )
    except Exception as e:
        return PythonExecutorOutput(
            stdout="",
            stderr=f"An unexpected error occurred in the executor: {str(e)}",
            exit_code=1
        )
