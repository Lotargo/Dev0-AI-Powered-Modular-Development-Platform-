"""
This module provides a standardized way to run bash commands and capture
their output.
"""
import subprocess
from pydantic import BaseModel

class BashResult(BaseModel):
    """Data model for the result of a bash command execution."""
    exit_code: int
    stdout: str
    stderr: str

def run_in_bash_session(command: str) -> BashResult:
    """
    Runs a shell command and captures its stdout, stderr, and exit code.
    """
    try:
        process = subprocess.run(
            command,
            shell=True,
            check=False,  # We handle the exit code manually
            capture_output=True,
            text=True,
            timeout=300
        )
        return BashResult(
            exit_code=process.returncode,
            stdout=process.stdout,
            stderr=process.stderr
        )
    except Exception as e:
        return BashResult(exit_code=1, stdout="", stderr=str(e))
