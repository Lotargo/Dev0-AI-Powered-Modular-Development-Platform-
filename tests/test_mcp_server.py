import unittest
from unittest.mock import MagicMock, patch, AsyncMock
import sys
import os
import asyncio
from project.core.mcp.server import create_app

class TestMCPServer(unittest.IsolatedAsyncioTestCase):

    @patch("project.core.mcp.server.asyncio.create_subprocess_exec")
    @patch("project.core.mcp.server.asyncio.to_thread")
    @patch("project.core.mcp.server.os.path.exists")
    @patch("project.core.mcp.server.os.makedirs")
    async def test_create_app_success(self, mock_makedirs, mock_exists, mock_to_thread, mock_subprocess):
        # Setup mocks
        mock_exists.side_effect = lambda p: True # Always exist

        # Mock subprocess
        mock_process = AsyncMock()
        mock_process.communicate.return_value = (
            b"Some logs...\nProject compiled to /tmp/compiled_project\nMore logs...",
            b""
        )
        mock_process.returncode = 0
        mock_subprocess.return_value = mock_process

        # Execute tool
        result = await create_app("Make a snake game", "/tmp/output")

        # Assertions
        self.assertIn("Success!", result)
        self.assertIn("/tmp/output/compiled_project.zip", result)

        # Check if subprocess was called
        mock_subprocess.assert_called_once()

        # Check zipping was called
        mock_to_thread.assert_called_once()

    @patch("project.core.mcp.server.asyncio.create_subprocess_exec")
    @patch("project.core.mcp.server.os.path.exists")
    async def test_create_app_failure_no_path(self, mock_exists, mock_subprocess):
        mock_exists.return_value = True

        mock_process = AsyncMock()
        mock_process.communicate.return_value = (
            b"Error: Something went wrong. No compiled path.",
            b""
        )
        mock_process.returncode = 0
        mock_subprocess.return_value = mock_process

        result = await create_app("Fail task", "/tmp/output")

        self.assertIn("Orchestrator failed to return a compiled path", result)

if __name__ == '__main__':
    unittest.main()
