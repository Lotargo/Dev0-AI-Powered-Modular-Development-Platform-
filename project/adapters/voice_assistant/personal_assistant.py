"""This module provides a collection of personal assistant tools.
"""
import asteval
from pydantic import BaseModel


class PersonalTools(BaseModel):
    """A collection of personal assistant tools.
    This class provides a set of tools that the voice assistant can use to
    help the user with personal tasks. It includes a reminder setter, a note
    creator, and a calculator.
    """

    def set_reminder(self, text: str, minutes: int) -> str:
        """Sets a reminder.
        This is an in-memory reminder, so it will be lost when the application
        is closed.
        Args:
            text: The text of the reminder.
            minutes: The number of minutes from now to set the reminder.
        Returns:
            A string confirming the reminder has been set.
        """
        return f"I will remind you in {minutes} minutes: '{text}'"

    def create_note(self, text: str) -> str:
        """Creates a note.
        This is an in-memory note, so it will be lost when the application
        is closed.
        Args:
            text: The text of the note.
        Returns:
            A string confirming the note has been created.
        """
        return f"Note created: '{text}'"

    def calculator(self, expression: str) -> str:
        """Calculates the result of a mathematical expression.
        This method uses the `asteval` library to safely evaluate mathematical
        expressions.
        Args:
            expression: The mathematical expression to evaluate.
        Returns:
            A string with the result of the calculation, or an error message
            if the expression is invalid.
        """
        aeval = asteval.Interpreter()
        try:
            result = aeval.eval(expression)
            return f"{expression} = {result}"
        except:
            return "Sorry, I couldn't calculate that."
