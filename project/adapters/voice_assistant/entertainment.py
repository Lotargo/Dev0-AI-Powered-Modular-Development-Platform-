"""This module provides a collection of entertainment tools for the voice
assistant.
"""
import random
from pydantic import BaseModel


class EntertainmentTools(BaseModel):
    """A collection of entertainment tools.
    This class provides a set of tools that the voice assistant can use to
    entertain the user. It includes a joke teller and a simple game player.
    """

    def tell_joke(self) -> str:
        """Tells a random joke.
        Returns:
            A string containing a random joke.
        """
        jokes = [
            "Why don't scientists trust atoms? Because they make up everything!",
            "I told my wife she should embrace her mistakes. She gave me a hug.",
            "Why did the scarecrow win an award? Because he was outstanding in his field!",
        ]
        return random.choice(jokes)

    def play_game(self, game: str) -> str:
        """Starts a mini-game.
        Args:
            game: The name of the game to play.
        Returns:
            A string with the game's content.
        """
        if "riddle" in game.lower():
            return "I have cities, but no houses; forests, but no trees; and water, but no fish. What am I? ... A map."
        elif "quiz" in game.lower():
            return "What is the capital of France? ... Paris!"
        else:
            return "I don't know that game, but we can try riddles or a quiz!"
