import os
import shutil
import asyncio
import sys
import re
import zipfile
from typing import Optional
from mcp.server.fastmcp import FastMCP

# Initialize FastMCP server
mcp = FastMCP("Dev0 Architect")

def strip_ansi(text: str) -> str:
    """Strips ANSI escape codes from text."""
    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    return ansi_escape.sub('', text)

@mcp.tool()
async def create_app(task_prompt: str, output_dir: str) -> str:
    """
    Creates a full-stack application (MVP) based on the task prompt using the Dev0 Architect.

    Args:
        task_prompt: The description of the application to build.
        output_dir: The absolute path where the final zipped project should be saved.

    Returns:
        A status message indicating success or failure, including the path to the saved file.
    """
    # Use sys.stderr for logging to avoid corrupting stdout (JSON-RPC)
    sys.stderr.write(f"Received task: {task_prompt}\n")
    sys.stderr.write(f"Target output directory: {output_dir}\n")

    # 1. Validate Output Directory
    if not os.path.exists(output_dir):
        try:
            os.makedirs(output_dir, exist_ok=True)
        except Exception as e:
            return f"Error: Could not create output directory '{output_dir}'. Details: {e}"

    # 2. Construct Command to Run Orchestrator
    # We call run_orchestrator.py which handles logic and calls run_architect.py
    # We assume we are in the project root.
    project_root = os.getcwd()
    script_path = os.path.join(project_root, "run_orchestrator.py")

    if not os.path.exists(script_path):
        return f"Error: Could not find 'run_orchestrator.py' at {script_path}. Are you running from the project root?"

    # Using 'python' directly as we assume we are already in the virtual environment
    # if the server is running via poetry.
    cmd = [sys.executable, script_path, task_prompt]

    sys.stderr.write(f"Executing command: {' '.join(cmd)}\n")

    try:
        # Run the orchestrator asynchronously
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=project_root
        )

        stdout_bytes, stderr_bytes = await process.communicate()
        stdout_raw = stdout_bytes.decode()
        stderr = stderr_bytes.decode()

        # Strip ANSI codes for robust parsing
        stdout = strip_ansi(stdout_raw)

        # 3. Parse Output for "Project compiled to <path>"
        # Pattern from run_architect.py: "Project compiled to {compiled_project_path}"
        match = re.search(r"Project compiled to\s+(.+)", stdout)

        if not match:
            # If regex fails, check if we have an error in stderr or stdout
            error_msg = f"Orchestrator failed to return a compiled path.\n\nExit Code: {process.returncode}\n\nSTDOUT:\n{stdout[-1000:]}\n\nSTDERR:\n{stderr[-1000:]}"
            return error_msg

        compiled_path = match.group(1).strip()
        sys.stderr.write(f"Detected compiled project at: {compiled_path}\n")

        if not os.path.exists(compiled_path):
            return f"Error: Orchestrator reported path '{compiled_path}' but it does not exist."

        # 4. Zip the Generated Project
        project_name = os.path.basename(compiled_path)
        zip_filename = f"{project_name}.zip"
        zip_filepath = os.path.join(output_dir, zip_filename)

        sys.stderr.write(f"Zipping to: {zip_filepath}\n")

        try:
            # Run zip operation in a thread to avoid blocking the async loop
            await asyncio.to_thread(
                shutil.make_archive,
                base_name=os.path.splitext(zip_filepath)[0],
                format='zip',
                root_dir=os.path.dirname(compiled_path),
                base_dir=os.path.basename(compiled_path)
            )
        except Exception as e:
            return f"Error creating zip file: {e}"

        return f"Success! Application built and saved to: {zip_filepath}"

    except Exception as e:
        return f"Critical Server Error: {str(e)}"
