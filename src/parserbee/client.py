"""HTTP client for the ParserBee API."""

import mimetypes
import os
from pathlib import Path
from typing import IO, Any, Dict, Optional, Union

import requests

from . import __version__
from .errors import APIConnectionError, APIError, error_for_status

DEFAULT_BASE_URL = "https://app.parserbee.com"
DEFAULT_TIMEOUT = 120.0

FileInput = Union[str, os.PathLike, IO[bytes]]


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

    def extract(
        self,
        template_id: str,
        file: Optional[FileInput] = None,
        *,
        file_url: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Extract structured data from a document with a Parser Template.

        Pass either ``file`` (a path or an open binary file) or ``file_url``
        (a public link to the document). Each extraction costs 1 page credit
        per page processed.

        Returns the full API response. The extracted fields are in
        ``result["data"]``; ``result["usage"]`` holds the page count and the
        page credits charged.
        """
        if not template_id:
            raise ValueError("template_id is required")
        if (file is None) == (file_url is None):
            raise ValueError("Pass exactly one of file or file_url")

        if file_url is not None:
            return self._request(
                "POST",
                "/api/v1/extract",
                json={"template_id": template_id, "file_url": file_url},
            )

        if isinstance(file, (str, os.PathLike)):
            path = Path(file)
            with path.open("rb") as handle:
                return self._upload(template_id, handle, path.name)

        name = Path(getattr(file, "name", "document")).name
        return self._upload(template_id, file, name)

    def _upload(self, template_id: str, handle: IO[bytes], name: str) -> Dict[str, Any]:
        content_type = mimetypes.guess_type(name)[0] or "application/octet-stream"
        return self._request(
            "POST",
            "/api/v1/extract",
            data={"template_id": template_id},
            files={"file": (name, handle, content_type)},
        )

    def close(self) -> None:
        """Close the underlying HTTP session."""
        self._session.close()

    def __enter__(self) -> "ParserBee":
        return self

    def __exit__(self, *exc: Any) -> None:
        self.close()
