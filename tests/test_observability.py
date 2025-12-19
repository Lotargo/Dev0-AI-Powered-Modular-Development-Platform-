import unittest
from unittest.mock import MagicMock, patch, AsyncMock
import json
from project.core.framework.observability import observable, get_event_bus, Event, RedisEventBus

class TestObservability(unittest.IsolatedAsyncioTestCase):

    @patch("project.core.framework.observability.redis.from_url")
    async def test_observable_decorator(self, mock_redis):
        # Setup Redis mock to support await
        mock_client = MagicMock()
        mock_client.publish = AsyncMock() # Make publish awaitable
        mock_redis.return_value = mock_client

        # Reset singleton to ensure fresh mock
        import project.core.framework.observability as obs
        obs._bus_instance = None

        # Define decorated function
        @observable(source_name="TestFunc")
        async def dummy_func(x, y):
            return x + y

        # Execute
        result = await dummy_func(3, 5)

        # Verify Result
        self.assertEqual(result, 8)

        # Verify Redis calls (Publish START and COMPLETE)
        self.assertEqual(mock_client.publish.call_count, 2)

        # Check First Call (START)
        args_start, _ = mock_client.publish.call_args_list[0]
        channel, message_json = args_start
        event_start = json.loads(message_json)
        self.assertEqual(event_start["type"], "EXECUTION_START")
        self.assertEqual(event_start["source"], "TestFunc")
        self.assertIn("3", event_start["data"]["args"])

        # Check Second Call (COMPLETE)
        args_end, _ = mock_client.publish.call_args_list[1]
        channel, message_json = args_end
        event_end = json.loads(message_json)
        self.assertEqual(event_end["type"], "EXECUTION_COMPLETE")
        self.assertEqual(event_end["source"], "TestFunc")
        self.assertIn("duration", event_end["data"])

    @patch("project.core.framework.observability.redis.from_url")
    async def test_observable_error(self, mock_redis):
        mock_client = MagicMock()
        mock_client.publish = AsyncMock() # Make publish awaitable
        mock_redis.return_value = mock_client

        import project.core.framework.observability as obs
        obs._bus_instance = None

        @observable(source_name="ErrorFunc")
        async def fail_func():
            raise ValueError("Test Error")

        with self.assertRaises(ValueError):
            await fail_func()

        # Should have START and ERROR events
        self.assertEqual(mock_client.publish.call_count, 2)

        args_err, _ = mock_client.publish.call_args_list[1]
        event_err = json.loads(args_err[1])
        self.assertEqual(event_err["type"], "EXECUTION_ERROR")
        self.assertEqual(event_err["data"]["error"], "Test Error")

if __name__ == "__main__":
    unittest.main()
