"""Python client for the ParserBee document extraction API."""

__version__ = "0.1.0"

from .client import ParserBee  # noqa: E402
from .errors import (  # noqa: E402
    APIConnectionError,
    APIError,
    AuthenticationError,
    InsufficientCreditsError,
    InvalidRequestError,
    NotFoundError,
    ParserBeeError,
    PermissionDeniedError,
)

__all__ = [
    "ParserBee",
    "ParserBeeError",
    "APIError",
    "APIConnectionError",
    "AuthenticationError",
    "InsufficientCreditsError",
    "InvalidRequestError",
    "NotFoundError",
    "PermissionDeniedError",
]
