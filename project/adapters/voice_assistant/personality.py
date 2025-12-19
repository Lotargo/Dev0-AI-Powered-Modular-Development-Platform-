"""This module provides personality features for the voice assistant.
It includes an emotion engine to add personality to responses, and a
personality class that defines Alice's personality traits and catchphrases.
"""
import random


class EmotionEngine:
    """A simple emotion engine to add personality to responses.
    This class is used to add emotional flavor to the voice assistant's
    responses. It maintains a mood and uses it to select a suitable
    emotional phrase to prepend to the response.
    """

    def __init__(self):
        """Initializes the EmotionEngine with a default mood."""
        self.mood = "friendly"

    def respond_with_emotion(self, text: str) -> str:
        """Adds an emotional phrase to the beginning of a response.
        Args:
            text: The response text.
        Returns:
            The response text with an emotional phrase prepended.
        """
        emotions = {
            "friendly": ["Of course!", "With pleasure!", "Happy to help!"],
            "cheerful": ["Oh, easy!", "Let's do it!", "And... done!"],
        }
        prefix = random.choice(emotions.get(self.mood, ["Okay."]))
        return f"{prefix} {text}"


class AlicePersonality:
    """Defines Alice's personality traits and catchphrases.
    This class is used to add a consistent personality to the voice
    assistant's responses. It includes a list of catchphrases that can be
    appended to the end of a response.
    """

    def __init__(self):
        """Initializes the AlicePersonality with a list of catchphrases."""
        self.catchphrases = [
            "Here is what I found.",
            "My pleasure!",
            "I can offer this.",
            "Excellent choice!",
        ]

    def personalize_response(self, response: str) -> str:
        """Adds a catchphrase to the end of a response.
        Args:
            response: The response text.
        Returns:
            The response text with a catchphrase appended.
        """
        phrase = random.choice(self.catchphrases)
        return f"{response} {phrase}"
