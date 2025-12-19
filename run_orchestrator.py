"""
Main Entry Point: Smart Orchestrator (The "Switch")
Decides whether to use Classic Mode (Constructor) or Research Mode (Creator).
"""
import argparse
import asyncio
import os
import sys
import subprocess
from dotenv import load_dotenv

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from project.core.llm_gateway.gateway import execute as gateway_execute
from project.core.memory.qdrant_manager import get_qdrant_manager
from project.core.framework.observability import observable

@observable
async def decide_mode(task: str) -> str:
    """
    Decides which mode to run based on available tools.
    Returns: 'classic' or 'research'
    """
    qm = get_qdrant_manager()
    tools = qm.search_tools(task, limit=10)
    tools_json = "\n".join([f"- {t['name']}: {t.get('description', '')}" for t in tools])

    prompt = f"""
You are the Chief Architect of the Dev0 system.
Your goal is to route the user's task to the correct team.

**User Task:** "{task}"

**Available Atomic Blocks (Tools):**
{tools_json}

**Routing Rules:**
1.  **Classic Mode (Constructor):** Use this if the task can be solved by combining the available tools (e.g., file ops, search, simple logic). The system CANNOT install new libraries in this mode.
2.  **Research Mode (Creator):** Use this if the task requires:
    *   Creating a NEW tool/module from scratch.
    *   Installing NEW external Python libraries (e.g., numpy, pandas, pyqrcode) that are not in the tools list.
    *   Complex logic that doesn't fit existing blocks.

**Decision:**
Reply with EXACTLY one word: "CLASSIC" or "RESEARCH".
"""
    # Use a reasoning model for this decision
    try:
        response = await gateway_execute(model_group="reasoning_model_group", prompt=prompt)
        decision = response.strip().upper()

        if "RESEARCH" in decision:
            return "research"
        return "classic"
    except Exception as e:
        print(f"Orchestrator Warning: Router failed ({e}). Defaulting to RESEARCH.")
        return "research"

def main():
    parser = argparse.ArgumentParser(description="Dev0 Smart Orchestrator")
    parser.add_argument("task", type=str, help="The task to execute.")
    parser.add_argument("--profile", choices=["standard", "weak"], default="standard", help="Model profile.")
    args = parser.parse_args()

    load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

    print(f"--- Orchestrator: Analyzing Task '{args.task}' ---")

    # async run decision
    mode = asyncio.run(decide_mode(args.task))
    print(f"--- Decision: {mode.upper()} Mode ---")

    # Close Qdrant to release lock for subprocess
    qm = get_qdrant_manager()
    if hasattr(qm, 'close'):
        qm.close()
    elif hasattr(qm, 'client') and hasattr(qm.client, 'close'):
        qm.client.close()

    # Call run_architect.py
    cmd = ["poetry", "run", "python", "run_architect.py", args.task, "--mode", mode, "--profile", args.profile]

    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Orchestrator: Subprocess failed with code {e.returncode}")
        sys.exit(e.returncode)

if __name__ == "__main__":
    main()
