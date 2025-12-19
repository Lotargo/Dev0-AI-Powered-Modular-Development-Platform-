import asyncio
import argparse
import sys
import os
import shutil
from typing import Optional
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.client.sse import sse_client

async def run_client(transport_mode: str, command: Optional[str] = None, url: Optional[str] = None):
    print(f"--- Starting MCP Client Test (Transport: {transport_mode.upper()}) ---")

    # Define the interaction logic as a reusable function
    async def interact(session: ClientSession):
        print("\n> Initializing session...")
        await session.initialize()

        print("\n> Listing tools...")
        tools_result = await session.list_tools()
        tools = tools_result.tools
        print(f"Found {len(tools)} tools:")
        for tool in tools:
            print(f" - {tool.name}: {tool.description}")

        # Verify 'create_app' exists
        tool_names = [t.name for t in tools]
        if "create_app" not in tool_names:
            print("ERROR: 'create_app' tool not found!")
            return False

        # Prepare execution
        task_prompt = "Create a simple Python script named 'hello.py' that prints 'Hello from MCP'"
        output_dir = os.path.abspath("test_mcp_output")

        # Clean up previous run
        if os.path.exists(output_dir):
            shutil.rmtree(output_dir)
        os.makedirs(output_dir, exist_ok=True)

        print(f"\n> Calling tool 'create_app'...")
        print(f"  Task: {task_prompt}")
        print(f"  Output Dir: {output_dir}")

        try:
            # Call the tool
            result = await session.call_tool(
                "create_app",
                arguments={
                    "task_prompt": task_prompt,
                    "output_dir": output_dir
                }
            )

            print("\n> Tool Execution Result:")
            # MCP tool result content is a list of TextContent or ImageContent
            content_text = ""
            for content in result.content:
                if hasattr(content, 'text'):
                    print(content.text)
                    content_text += content.text

            # Verification
            if "Error" in content_text:
                print("\nFAILURE: Tool returned an error.")
                return False

            # Check filesystem
            zip_path = os.path.join(output_dir, "compiled_project.zip")
            # Note: The server output might name the zip differently based on the folder name
            # The server logic is: zip_filename = f"{project_name}.zip"
            # We need to check if ANY zip exists
            zips = [f for f in os.listdir(output_dir) if f.endswith('.zip')]

            if not zips:
                print(f"\nFAILURE: No ZIP file found in {output_dir}")
                return False

            print(f"\nSUCCESS: Found generated artifact: {zips[0]}")
            return True

        except Exception as e:
            print(f"\nEXCEPTION during tool call: {e}")
            return False

    # Execute based on transport
    try:
        if transport_mode == "stdio":
            if not command:
                raise ValueError("Command is required for stdio transport")

            # Parse command string into list
            import shlex
            cmd_parts = shlex.split(command)

            server_params = StdioServerParameters(
                command=cmd_parts[0],
                args=cmd_parts[1:],
                env=None
            )

            async with stdio_client(server_params) as (read, write):
                async with ClientSession(read, write) as session:
                    return await interact(session)

        elif transport_mode == "sse":
            if not url:
                raise ValueError("URL is required for sse transport")

            async with sse_client(url) as (read, write):
                async with ClientSession(read, write) as session:
                    return await interact(session)

    except Exception as e:
        print(f"Client Error: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description="MCP Test Client")
    parser.add_argument("--transport", choices=["stdio", "sse"], required=True)
    parser.add_argument("--command", help="Command to run server (for stdio)")
    parser.add_argument("--url", help="URL of server (for sse)")

    args = parser.parse_args()

    success = asyncio.run(run_client(args.transport, args.command, args.url))

    if success:
        print("\n*** TEST PASSED ***")
        sys.exit(0)
    else:
        print("\n*** TEST FAILED ***")
        sys.exit(1)

if __name__ == "__main__":
    main()
