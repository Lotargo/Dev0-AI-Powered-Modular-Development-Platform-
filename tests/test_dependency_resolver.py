
import sys
import os
import pytest
from unittest.mock import patch, MagicMock

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from project.core.infrastructure.dependency_resolver import DependencyResolver

@pytest.fixture
def resolver():
    with patch.dict(os.environ, {"TAVILY_API_KEY": "fake_key"}):
        return DependencyResolver()

def test_resolve_known_package(resolver):
    # Should return from cache without API call
    assert resolver.resolve("PIL") == "Pillow"
    assert resolver.resolve("cv2") == "opencv-python"

def test_resolve_pypi_via_tavily_mock_success(resolver):
    # Mock httpx.post to simulate Tavily response
    mock_response = {
        "answer": "You can install it via `pip install some-weird-package`.",
        "results": [
            {"url": "https://pypi.org/project/some-weird-package/", "content": "The official package."}
        ]
    }

    with patch("httpx.post") as mock_post:
        mock_post.return_value.raise_for_status = MagicMock()
        mock_post.return_value.json.return_value = mock_response

        pkg = resolver.resolve("some_weird_import")
        assert pkg == "some-weird-package"

        # Verify cache update
        assert resolver.cache["some_weird_import"] == "some-weird-package"

def test_resolve_pypi_fallback(resolver):
    # Mock httpx.post to return nothing useful
    mock_response = {
        "answer": "I don't know.",
        "results": []
    }

    with patch("httpx.post") as mock_post:
        mock_post.return_value.raise_for_status = MagicMock()
        mock_post.return_value.json.return_value = mock_response

        # Should fall back to the import name itself
        pkg = resolver.resolve("unknown_pkg")
        assert pkg == "unknown_pkg"
