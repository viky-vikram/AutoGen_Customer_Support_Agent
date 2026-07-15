"""Custom exception types for the Vikram AI Tech support application.

Each exception carries a ``user_message`` that is safe to display in the UI.
Technical details belong in logs, never in the user-facing message.
"""

from __future__ import annotations


class SupportAppError(Exception):
    """Base class for all application-specific errors."""

    default_user_message = "Something went wrong. Please try again in a moment."

    def __init__(self, message: str = "", user_message: str | None = None) -> None:
        super().__init__(message or self.default_user_message)
        self.user_message = user_message or self.default_user_message


class ConfigurationError(SupportAppError):
    """Raised when required configuration is missing or invalid."""

    default_user_message = (
        "The application is not configured correctly. "
        "Please check the environment settings (see README) and restart."
    )


class EmptyInputError(SupportAppError):
    """Raised when the user submits an empty or whitespace-only message."""

    default_user_message = "Please enter a question so I can help you."


class RoutingError(SupportAppError):
    """Raised when the manager agent fails to produce a usable routing decision."""

    default_user_message = (
        "I could not determine the right department for your question. "
        "Please try rephrasing it."
    )


class AgentExecutionError(SupportAppError):
    """Raised when a department agent fails to produce a response."""

    default_user_message = (
        "The support specialist could not complete your request right now. "
        "Please try again shortly."
    )


class DocumentGenerationError(SupportAppError):
    """Raised when project-document generation (PDF / chart) fails."""

    default_user_message = "Document generation failed. Please check the logs."
