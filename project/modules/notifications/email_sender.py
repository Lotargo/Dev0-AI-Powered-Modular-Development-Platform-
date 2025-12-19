"""This module provides a function to send an email.
"""
from pydantic import BaseModel, Field


class EmailSenderInput(BaseModel):
    """Input model for the email_sender function.
    Attributes:
        email: The recipient's email address.
        subject: The subject of the email.
        message: The content of the email.
    """
    email: str = Field(..., description="The recipient's email address")
    subject: str = Field(..., description="The subject of the email")
    message: str = Field(..., description="The content of the email")


class EmailSenderOutput(BaseModel):
    """Output model for the email_sender function.
    Attributes:
        status: The status of the email sending operation.
    """
    status: str = Field(..., description="The status of the email sending operation")


def execute(input_data: EmailSenderInput) -> EmailSenderOutput:
    """Sends an email.
    Args:
        input_data: An EmailSenderInput object with the email details.
    Returns:
        An EmailSenderOutput object with the status of the operation.
    """
    print(f"Sending email to {input_data.email} with subject '{input_data.subject}' and message '{input_data.message}'")
    return EmailSenderOutput(status="sent")
