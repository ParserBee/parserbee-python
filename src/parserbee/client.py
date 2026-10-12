"""HTTP client for the ParserBee API."""

import os
from typing import Any, Dict, Optional

import requests

from . import __version__
from .errors import APIConnectionError, APIError, error_for_status

DEFAULT_BASE_URL = "https://app.parserbee.com"
DEFAULT_TIMEOUT = 120.0


class ParserBee:
    """Client for the ParserBee REST API.

    The API key is read from the ``api_key`` argument or, if that is not
    given, from the ``PARSERBEE_API_KEY`` environment variable. Generate a
    key from Settings in the ParserBee dashboard; it starts with ``pk_``.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        *,
        base_url: str = DEFAULT_BASE_URL,
        timeout: float = DEFAULT_TIMEOUT,
        session: Optional[requests.Session] = None,
    ) -> None:
        api_key = api_key or os.environ.get("PARSERBEE_API_KEY")
        if not api_key:
            raise ValueError(
                "No API key given. Pass api_key=... or set PARSERBEE_API_KEY."
            )
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self._session = session or requests.Session()
        self._session.headers.update(
            {
                "x-api-key": api_key,
                "User-Agent": f"parserbee-python/{__version__}",
                "Accept": "application/json",
            }
        )

    def _request(self, method: str, path: str, **kwargs: Any) -> Dict[str, Any]:
        url = f"{self.base_url}{path}"
        kwargs.setdefault("timeout", self.timeout)
        try:
            response = self._session.request(method, url, **kwargs)
        except requests.RequestException as exc:
            raise APIConnectionError(f"Could not reach the ParserBee API: {exc}") from exc

        try:
            body = response.json()
        except ValueError:
            body = {}

        if response.status_code >= 400:
            raise error_for_status(response.status_code, body)
        if not isinstance(body, dict):
            raise APIError(
                "Unexpected response from the ParserBee API",
                status=response.status_code,
            )
        return body

    def close(self) -> None:
        """Close the underlying HTTP session."""
        self._session.close()

    def __enter__(self) -> "ParserBee":
        return self

    def __exit__(self, *exc: Any) -> None:
        self.close()
