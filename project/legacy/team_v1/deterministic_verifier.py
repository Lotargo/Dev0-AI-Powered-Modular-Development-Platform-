"""
Verifier Agent: An agent that analyzes a compiled project by running it to ensure its integrity.
"""
import asyncio
import os
import logging
import shutil
from pydantic import BaseModel

from project.modules.tools.python_executor import execute as execute_python, PythonExecutorInput

class Input(BaseModel):
    project_path: str

class Output(BaseModel):
    status: str
    message: str

async def execute_async(input_data: Input) -> Output:
    """
    Runs the compiled project to verify its integrity. If verification fails,
    it cleans up the project directory.
    """
    project_path = input_data.project_path
    print(f"--- Verifier Agent: Starting verification of project at '{project_path}' ---")

    try:
        # The main entry point for the compiled project is always run.py
        run_script_path = os.path.join(project_path, "run.py")

        if not os.path.exists(run_script_path):
            raise FileNotFoundError(f"Could not find entry point 'run.py' in project path: {project_path}")

        # Execute the main script of the compiled project
        execution_code = f"""
import os
import subprocess

try:
    os.chdir('{project_path}')
    result = subprocess.run(
        ['poetry', 'run', 'python', 'run.py'],
        capture_output=True,
        text=True,
        check=True
    )
    print(result.stdout)
except subprocess.CalledProcessError as e:
    print("Execution failed. See stderr below:")
    print(e.stderr)
    raise e
"""

        python_input = PythonExecutorInput(code=execution_code)
        result = execute_python(python_input)

        if result.exit_code != 0:
            error_message = (
                f"Project execution failed.\\n"
                f"--- Target Process STDERR (captured in Executor STDOUT) ---\\n{result.stdout}\\n"
                f"--- Executor Process STDERR ---\\n{result.stderr}"
            )
            print(error_message)

            # Clean up the failed MVP project directory
            print(f"Cleaning up failed project at: {project_path}")
            shutil.rmtree(project_path)

            return Output(status="error", message=error_message)

        success_message = "Project executed successfully. Verification passed."
        print(success_message)
        return Output(status="success", message=success_message)

    except Exception as e:
        error_message = f"An unexpected error occurred during verification: {e}"
        logging.error(error_message)

        # Also clean up if an unexpected error occurs
        if os.path.exists(project_path):
            print(f"Cleaning up project due to unexpected error at: {project_path}")
            shutil.rmtree(project_path)

        return Output(status="error", message=error_message)

def execute(input_data: Input) -> Output:
    return asyncio.run(execute_async(input_data))
