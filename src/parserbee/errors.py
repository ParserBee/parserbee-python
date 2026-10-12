"""Exceptions raised by the ParserBee client."""

from typing import Any, Dict, Optional


class ParserBeeError(Exception):
    """Base class for every error the client raises."""

    def __init__(
        self,
        message: str,
        *,
        code: Optional[str] = None,
        status: Optional[int] = None,
        body: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.code = code
        self.status = status
        self.body = body or {}

    def __str__(self) -> str:
        parts = [self.message]
        if self.code:
            parts.append(f"(code: {self.code})")
        if self.status:
            parts.append(f"[HTTP {self.status}]")
        return " ".join(parts)


class AuthenticationError(ParserBeeError):
    """The API key is missing or invalid (HTTP 401)."""


class InsufficientCreditsError(ParserBeeError):
    """The account has no page credits left (HTTP 402)."""

    @property
    def credits_remaining(self) -> Optional[int]:
        return self.body.get("credits_remaining")


class PermissionDeniedError(ParserBeeError):
    """No active subscription, or the account is locked (HTTP 403)."""


class NotFoundError(ParserBeeError):
    """The template or activity record does not exist (HTTP 404)."""


class InvalidRequestError(ParserBeeError):
    """The request is missing a field or the file is not accepted (HTTP 400)."""


class APIError(ParserBeeError):
    """Any other error returned by the API, including server errors."""


class APIConnectionError(ParserBeeError):
    """The request did not reach the API (network error or timeout)."""


_STATUS_ERRORS = {
    400: InvalidRequestError,
    401: AuthenticationError,
    402: InsufficientCreditsError,
    403: PermissionDeniedError,
    404: NotFoundError,
}


def error_for_status(status: int, body: Dict[str, Any]) -> ParserBeeError:
    """Build the right exception for an error response."""
    cls = _STATUS_ERRORS.get(status, APIError)
    message = body.get("error") or f"ParserBee API returned HTTP {status}"
    return cls(message, code=body.get("code"), status=status, body=body)
