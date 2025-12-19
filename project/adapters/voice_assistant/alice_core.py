"""This module is the core of the voice assistant Alice.
It integrates various tools and personality features to process commands and
generate responses.
"""
from pydantic import BaseModel, Field
from .personal_assistant import PersonalTools
from .entertainment import EntertainmentTools
from .music_player import MusicPlayerTool
from .search_tools import SafeSearchTool
from .personality import EmotionEngine, AlicePersonality
from .conversation_context import ConversationContext
import re


class AliceCoreInput(BaseModel):
    """Input model for the Alice core.
    Attributes:
        command: The command to be processed by Alice.
    """
    command: str = Field(..., description="The command to be processed by Alice")


class AliceCoreOutput(BaseModel):
    """Output model for the Alice core.
    Attributes:
        response: Alice's response to the command.
    """
    response: str = Field(..., description="Alice's response to the command")


class AliceRouter:
    """Routes commands to the appropriate tool and adds personality.
    This class is the central hub of Alice's functionality. It initializes
    all the available tools and routes incoming commands to the correct one.
    It also uses the EmotionEngine and AlicePersonality to make the responses
    more engaging and human-like.
    """

    def __init__(self):
        """Initializes the AliceRouter with all the necessary tools."""
        self.personal_assistant = PersonalTools()
        self.entertainment = EntertainmentTools()
        self.music_player = MusicPlayerTool()
        self.search_tools = SafeSearchTool()
        self.emotion_engine = EmotionEngine()
        self.personality = AlicePersonality()
        self.context = ConversationContext()

    def route(self, command: str) -> str:
        """Routes the command to the appropriate tool.
        This method takes a command as input, finds the appropriate tool to
        handle it, and then wraps the response with personality and emotion.
        Args:
            command: The command to be processed.
        Returns:
            Alice's response to the command.
        """
        response = self._route_command(command)
        emotional_response = self.emotion_engine.respond_with_emotion(response)
        return self.personality.personalize_response(emotional_response)

    def _route_command(self, command: str) -> str:
        """Internal router to find and execute the correct tool.
        This method uses a series of `if` statements to match the command
        to the appropriate tool. This is a simple routing strategy that can be
        expanded with more sophisticated NLP techniques in the future.
        Args:
            command: The command to be processed.
        Returns:
            The response from the selected tool.
        """
        command_lower = command.lower()

        # Context Management
        if "remember that" in command_lower:
            match = re.search(r"remember that my (.*?) is (.*)", command, re.IGNORECASE)
            if match:
                key = match.group(1).replace("'s name", "").strip()
                value = match.group(2).strip()
                self.context.remember(key, value)
                return f"I will remember that your {key} is {value}."
        if "what is my" in command_lower:
            key = command_lower.split("what is my ")[1].split("'s name")[0].strip()
            value = self.context.recall(key)
            if value:
                return f"Your {key} is {value}."
            else:
                return f"I don't remember your {key}."

        # Personal Assistant Tools
        if "calculate" in command_lower:
            expression = re.sub(r"calculate", "", command, flags=re.IGNORECASE).strip()
            return self.personal_assistant.calculator(expression)
        if "remind me to" in command_lower:
            match = re.search(r"remind me to (.*) in (\d+) minutes", command, re.IGNORECASE)
            if match:
                text = match.group(1).strip()
                minutes = int(match.group(2))
                return self.personal_assistant.set_reminder(text, minutes)
            else:
                return "Please specify the reminder in the format 'remind me to [task] in [number] minutes'."

        # Entertainment Tools
        if "joke" in command_lower:
            return self.entertainment.tell_joke()
        if "play a game" in command_lower:
            return self.entertainment.play_game("riddle")

        # Music Tools
        if "play on youtube" in command_lower:
            query = re.sub(r"play on youtube", "", command, flags=re.IGNORECASE).strip()
            return self.music_player.play_youtube(query)
        if "play radio" in command_lower:
            station = re.sub(r"play radio", "", command, flags=re.IGNORECASE).strip()
            return self.music_player.play_radio(station)

        # Search Tools
        if "weather in" in command_lower:
            city = re.sub(r".*weather in", "", command, flags=re.IGNORECASE).strip().replace("?", "")
            return self.search_tools.weather(city)
        if "news" in command_lower:
            return self.search_tools.news()

        return "Sorry, I don't understand that command."


# Global instance of the router
router = AliceRouter()


def execute(input_data: AliceCoreInput) -> AliceCoreOutput:
    """
    Processes a command sent to Alice and returns a response.
    This is the main entry point for the Alice module.
    Args:
        input_data: An AliceCoreInput object with the command to process.
    Returns:
        An AliceCoreOutput object with Alice's response.
    """
    response_text = router.route(input_data.command)
    return AliceCoreOutput(response=response_text)
