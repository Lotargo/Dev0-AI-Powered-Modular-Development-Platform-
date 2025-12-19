import pytest
from unittest.mock import patch, MagicMock
from project.recipes.agents.context_coder import execute_async as context_coder_execute
from project.recipes.agents.researcher import execute_async as researcher_execute
from project.recipes.agents.context_coder import ContextCoderInput
from project.recipes.agents.researcher import ResearcherInput

@pytest.mark.asyncio
async def test_context_coder_rag_injection():
    """
    Verifies that ContextCoder injects RAG content into the prompt.
    """
    # Mock Qdrant to return fake chunks
    with patch("project.recipes.agents.context_coder.get_qdrant_manager") as mock_get_qm:
        mock_qm = MagicMock()
        mock_get_qm.return_value = mock_qm

        mock_qm.search_items.side_effect = [
            # Codebase results
            [{"filepath": "fake_code.py", "content": "def fake(): pass"}],
            # Documentation results
            [{"filepath": "fake_doc.md", "content": "# Fake Doc"}]
        ]

        # Mock Gateway to inspect prompt
        with patch("project.recipes.agents.context_coder.gateway_execute") as mock_gateway:
            mock_gateway.return_value = "```python\ndef main(): pass\n```"

            input_data = ContextCoderInput(
                task_prompt="Create a file",
                research_context="Some context"
            )

            await context_coder_execute(input_data)

            # Assertions
            mock_qm.search_items.assert_any_call("codebase", "Create a file", limit=5)
            mock_qm.search_items.assert_any_call("documentation", "Create a file", limit=3)

            # Check prompt content
            call_args = mock_gateway.call_args
            prompt_sent = call_args.kwargs["prompt"]

            assert "**Reference Code (Project Style & Examples):**" in prompt_sent
            assert "fake_code.py" in prompt_sent
            assert "**Reference Documentation:**" in prompt_sent
            assert "fake_doc.md" in prompt_sent

@pytest.mark.asyncio
async def test_researcher_rag_injection():
    """
    Verifies that Researcher injects RAG content into the prompt.
    """
    # Mock Qdrant
    with patch("project.recipes.agents.researcher.get_qdrant_manager") as mock_get_qm:
        mock_qm = MagicMock()
        mock_get_qm.return_value = mock_qm

        mock_qm.search_items.side_effect = [
            [{"filepath": "existing_impl.py", "content": "class Existing: pass"}],
            [{"filepath": "philosophy.md", "content": "Do it this way"}]
        ]

        # Mock Gateway and Tavily
        with patch("project.recipes.agents.researcher.gateway_execute") as mock_gateway, \
             patch("project.recipes.agents.researcher.tavily_search") as mock_tavily:

            mock_gateway.return_value = "Research Summary"
            mock_tavily.return_value = MagicMock(results="Web results")

            input_data = ResearcherInput(topic="How to do X")

            await researcher_execute(input_data)

            # Assertions
            mock_qm.search_items.assert_any_call("codebase", "How to do X", limit=3)

            # Check prompt content
            call_args = mock_gateway.call_args
            prompt_sent = call_args.kwargs["prompt"]

            assert "**Local Codebase Context (Existing Implementations):**" in prompt_sent
            assert "existing_impl.py" in prompt_sent
            assert "**Local Documentation Context:**" in prompt_sent
            assert "philosophy.md" in prompt_sent
