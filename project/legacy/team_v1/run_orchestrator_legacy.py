"""
Main entry point for running the multi-agent team orchestrated by the state machine.
"""
import argparse
import asyncio
from datetime import datetime
from project.recipes.agents.orchestrator import execute_async as orchestrator_execute_async, Input as OrchestratorInput

async def main():
    """
    Initializes and runs the Orchestrator with a given task prompt.
    """
    parser = argparse.ArgumentParser(description="Run the AI agent orchestrator with a specific task.")
    parser.add_argument("task_prompt", type=str, help="The high-level task for the AI agent team to accomplish.")
    args = parser.parse_args()

    session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    print("--- Initializing AI Orchestrator ---")
    print(f"Goal: {args.task_prompt}")
    print(f"Session ID: {session_id}")
    print("------------------------------------")

    try:
        input_data = OrchestratorInput(task_prompt=args.task_prompt, session_id=session_id)
        result = await orchestrator_execute_async(input_data)

        print("\n--- Orchestrator Execution Finished ---")
        print(f"Final Status: {result.status}")
        print(f"Message: {result.message}")
        print("---------------------------------------")

    except Exception as e:
        print(f"\n--- An unhandled error occurred in the orchestrator ---")
        print(f"Error: {e}")
        print("---------------------------------------------------------")

if __name__ == "__main__":
    asyncio.run(main())
