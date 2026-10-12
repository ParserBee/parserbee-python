import io

import pytest
import requests

from parserbee import (
    APIConnectionError,
    AuthenticationError,
    InsufficientCreditsError,
    InvalidRequestError,
    NotFoundError,
    ParserBee,
)


class FakeResponse:
    def __init__(self, status_code, body):
        self.status_code = status_code
        self._body = body

    def json(self):
        if self._body is None:
            raise ValueError("no json")
        return self._body


class FakeSession:
    def __init__(self, response=None, error=None):
        self.headers = {}
        self.calls = []
        self.response = response or FakeResponse(200, {})
        self.error = error

    def request(self, method, url, **kwargs):
        self.calls.append((method, url, kwargs))
        if self.error:
            raise self.error
        return self.response

    def close(self):
        pass


def make_client(response=None, error=None):
    session = FakeSession(response, error)
    return ParserBee("pk_test", session=session), session


def test_api_key_from_environment(monkeypatch):
    monkeypatch.setenv("PARSERBEE_API_KEY", "pk_env")
    client = ParserBee(session=FakeSession())
    assert client.api_key == "pk_env"


def test_missing_api_key_raises(monkeypatch):
    monkeypatch.delenv("PARSERBEE_API_KEY", raising=False)
    with pytest.raises(ValueError):
        ParserBee(session=FakeSession())


def test_sends_api_key_header():
    client, session = make_client()
    assert session.headers["x-api-key"] == "pk_test"
    assert session.headers["User-Agent"].startswith("parserbee-python/")


def test_extract_uploads_file_from_path(tmp_path):
    pdf = tmp_path / "invoice.pdf"
    pdf.write_bytes(b"%PDF-1.4")
    body = {"success": True, "data": {"invoice_number": "INV-001"}}
    client, session = make_client(FakeResponse(200, body))

    result = client.extract("tpl_123", pdf)

    method, url, kwargs = session.calls[0]
    assert (method, url) == ("POST", "https://app.parserbee.com/api/v1/extract")
    assert kwargs["data"] == {"template_id": "tpl_123"}
    name, _, content_type = kwargs["files"]["file"]
    assert (name, content_type) == ("invoice.pdf", "application/pdf")
    assert result["data"]["invoice_number"] == "INV-001"


def test_extract_accepts_open_file():
    handle = io.BytesIO(b"\x89PNG")
    handle.name = "/tmp/receipt.png"
    client, session = make_client(FakeResponse(200, {"success": True}))

    client.extract("tpl_123", handle)

    name, _, content_type = session.calls[0][2]["files"]["file"]
    assert (name, content_type) == ("receipt.png", "image/png")


def test_extract_from_url_sends_json():
    client, session = make_client(FakeResponse(200, {"success": True}))

    client.extract("tpl_123", file_url="https://example.com/invoice.pdf")

    kwargs = session.calls[0][2]
    assert kwargs["json"] == {"template_id": "tpl_123", "file_url": "https://example.com/invoice.pdf"}
    assert "files" not in kwargs


@pytest.mark.parametrize("args", [{}, {"file": "a.pdf", "file_url": "https://x.y/a.pdf"}])
def test_extract_needs_exactly_one_source(args):
    client, _ = make_client()
    with pytest.raises(ValueError):
        client.extract("tpl_123", **args)


def test_list_templates_returns_items():
    client, session = make_client(FakeResponse(200, {"items": [{"id": "tpl_1"}], "total": 1}))
    assert client.list_templates() == [{"id": "tpl_1"}]
    assert session.calls[0][1].endswith("/api/v1/templates")


def test_get_template_escapes_id():
    client, session = make_client(FakeResponse(200, {"id": "a/b"}))
    client.get_template("a/b")
    assert session.calls[0][1].endswith("/api/v1/templates/a%2Fb")


def test_get_credits():
    client, _ = make_client(FakeResponse(200, {"credits_remaining": 42}))
    assert client.get_credits()["credits_remaining"] == 42


def test_activity_endpoints():
    client, session = make_client(FakeResponse(200, {"items": [], "total": 0}))
    assert client.list_activity() == []
    client.get_activity("req_1")
    assert session.calls[1][1].endswith("/api/v1/activity/req_1")


@pytest.mark.parametrize(
    "status,exc",
    [
        (400, InvalidRequestError),
        (401, AuthenticationError),
        (402, InsufficientCreditsError),
        (404, NotFoundError),
    ],
)
def test_error_statuses_map_to_exceptions(status, exc):
    client, _ = make_client(FakeResponse(status, {"error": "nope", "code": "SOME_CODE"}))
    with pytest.raises(exc) as info:
        client.get_credits()
    assert info.value.code == "SOME_CODE"
    assert info.value.status == status


def test_insufficient_credits_exposes_balance():
    body = {"error": "Insufficient page credits", "code": "INSUFFICIENT_CREDITS", "credits_remaining": 0}
    client, _ = make_client(FakeResponse(402, body))
    with pytest.raises(InsufficientCreditsError) as info:
        client.extract("tpl_123", file_url="https://example.com/a.pdf")
    assert info.value.credits_remaining == 0


def test_network_error_is_wrapped():
    client, _ = make_client(error=requests.ConnectionError("boom"))
    with pytest.raises(APIConnectionError):
        client.get_credits()
