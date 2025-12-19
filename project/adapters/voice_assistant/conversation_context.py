"""This module provides a simple in-memory context for a single conversation.
"""
from typing import Dict, Any


class ConversationContext:
    """A simple in-memory context for a single conversation.
    This class is used to store and retrieve information within a single
    conversation. It can be used to remember user preferences, previous
    interactions, or any other information that is relevant to the current
    conversation.
    """

    def __init__(self):
        """Initializes the ConversationContext with an empty context."""
        self.context: Dict[str, Any] = {}

    def remember(self, key: str, value: Any):
        """Stores a piece of information in the context.
        Args:
            key: The key to store the information under.
            value: The information to be stored.
        """
        self.context[key] = value

    def recall(self, key: str) -> Any:
        """Retrieves a piece of information from the context.
        Args:
            key: The key of the information to retrieve.
        Returns:
            The information associated with the key, or None if the key is
            not found.
        """
        return self.context.get(key)
