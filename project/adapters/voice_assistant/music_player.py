"""This module provides a safe music player that uses external APIs without
file system access.
"""
import os
from pydantic import BaseModel


class MusicPlayerTool(BaseModel):
    """A safe music player that uses external APIs.
    This class provides a set of tools for playing music from external
    sources like YouTube and online radio stations. It is designed to be
    safe, as it does not access the local file system.
    """

    def play_youtube(self, query: str) -> str:
        """Searches and plays music from YouTube.
        In a real implementation, this method would use the YouTube API to
        search for and play music. For now, it returns a mock response.
        Args:
            query: The search query for the music.
        Returns:
            A string indicating the music is playing.
        """
        # In a real implementation, you would use a library like `google-api-python-client`
        # api_key = os.getenv("YOUTUBE_API_KEY")
        # if not api_key:
        #     return "YouTube API key is not configured."
        return f"Now playing '{query}' on YouTube (mock)."

    def play_radio(self, station: str) -> str:
        """Plays an online radio station.
        This method simulates playing an online radio station. It checks if the
        requested station is in a predefined list and returns a mock response.
        Args:
            station: The name of the radio station to play.
        Returns:
            A string indicating the radio is playing, or an error message if
            the station is not found.
        """
        stations = {
            "europa plus": "https://ep-stream.com",
            "relax fm": "https://relax-fm-stream.com"
        }
        if station.lower() in stations:
            return f"Now playing {station} (mock)."
        else:
            return f"I don't know the radio station '{station}'."
