"""This module provides a simple email validation function.
It checks for the presence of the '@' symbol in an email address to determine
its validity.
"""
from pydantic import BaseModel, Field


class EmailValidatorInput(BaseModel):
    """Input model for the email validator.
    Attributes:
        email: The email address to be validated.
    """
    email: str = Field(..., description="The email address to validate")


class EmailValidatorOutput(BaseModel):
    """Output model for the email validator.
    Attributes:
        is_valid: A boolean indicating whether the email is valid.
        reason: A string explaining why the email is not valid.
    """
    is_valid: bool = Field(..., description="True if the email is valid, False otherwise")
    reason: str = Field(..., description="The reason why the email is not valid")


def execute(input_data: EmailValidatorInput) -> EmailValidatorOutput:
    """Validates an email address.
    This function checks if the provided email address contains the '@' symbol.
    While this is a basic check, it serves as a simple example of a validation module.
    Args:
        input_data: An EmailValidatorInput object containing the email to validate.
    Returns:
        An EmailValidatorOutput object indicating whether the email is valid,
        and a reason for the validation result.
    """
    if "@" in input_data.email:
        return EmailValidatorOutput(is_valid=True, reason="Valid email format")
    else:
        return EmailValidatorOutput(is_valid=False, reason="Invalid email format: missing '@' symbol")
