import pytest
import requests
import responses

from django_govbr_auth.client import GovBrOAuth2Client
from django_govbr_auth.exceptions import GovBrTokenError, GovBrUserInfoError


@pytest.fixture
def client():
    return GovBrOAuth2Client(
        client_id="my-client-id",
        client_secret="my-secret",
        redirect_uri="https://app.com/callback",
        base_url="https://sso.staging.acesso.gov.br/",
    )


def test_get_authorization_url(client):
    url = client.get_authorization_url("state123", "challenge456")
    assert "https://sso.staging.acesso.gov.br/authorize?" in url
    assert "client_id=my-client-id" in url
    assert "redirect_uri=https%3A%2F%2Fapp.com%2Fcallback" in url
    assert "state=state123" in url
    assert "code_challenge=challenge456" in url
    assert "code_challenge_method=S256" in url
    assert "scope=openid+email+profile" in url


@responses.activate
def test_exchange_code_for_token_success(client):
    responses.add(
        responses.POST,
        "https://sso.staging.acesso.gov.br/token",
        json={"access_token": "token123", "id_token": "idtoken456", "token_type": "Bearer"},
        status=200,
    )
    res = client.exchange_code_for_token("code123", "verifier123")
    assert res["access_token"] == "token123"
    assert res["id_token"] == "idtoken456"


@responses.activate
def test_exchange_code_for_token_http_error(client):
    responses.add(
        responses.POST,
        "https://sso.staging.acesso.gov.br/token",
        status=400,
    )
    with pytest.raises(GovBrTokenError) as exc_info:
        client.exchange_code_for_token("code123", "verifier123")
    assert "Token exchange failed" in str(exc_info.value)


def test_exchange_code_for_token_request_exception(client, monkeypatch):
    def mock_post(*args, **kwargs):
        raise requests.RequestException("Connection error")

    monkeypatch.setattr(client._session, "post", mock_post)
    with pytest.raises(GovBrTokenError) as exc_info:
        client.exchange_code_for_token("code123", "verifier123")
    assert "request error" in str(exc_info.value)


def test_exchange_code_for_token_unexpected_exception(client, monkeypatch):
    def mock_post(*args, **kwargs):
        raise RuntimeError("Unexpected error")

    monkeypatch.setattr(client._session, "post", mock_post)
    with pytest.raises(GovBrTokenError) as exc_info:
        client.exchange_code_for_token("code123", "verifier123")
    assert "unexpected error" in str(exc_info.value)


@responses.activate
def test_get_user_info_success(client):
    responses.add(
        responses.GET,
        "https://sso.staging.acesso.gov.br/userinfo",
        json={"sub": "12345678901", "name": "João Silva", "email": "joao@gov.br"},
        status=200,
    )
    res = client.get_user_info("token123")
    assert res["sub"] == "12345678901"
    assert res["name"] == "João Silva"


@responses.activate
def test_get_user_info_http_error(client):
    responses.add(
        responses.GET,
        "https://sso.staging.acesso.gov.br/userinfo",
        status=401,
    )
    with pytest.raises(GovBrUserInfoError) as exc_info:
        client.get_user_info("token123")
    assert "Failed to fetch user info" in str(exc_info.value)


def test_get_user_info_request_exception(client, monkeypatch):
    def mock_get(*args, **kwargs):
        raise requests.RequestException("Timeout")

    monkeypatch.setattr(client._session, "get", mock_get)
    with pytest.raises(GovBrUserInfoError) as exc_info:
        client.get_user_info("token123")
    assert "User info request error" in str(exc_info.value)


def test_get_user_info_unexpected_exception(client, monkeypatch):
    def mock_get(*args, **kwargs):
        raise ValueError("Invalid format")

    monkeypatch.setattr(client._session, "get", mock_get)
    with pytest.raises(GovBrUserInfoError) as exc_info:
        client.get_user_info("token123")
    assert "User info unexpected error" in str(exc_info.value)


def test_get_logout_url(client):
    url = client.get_logout_url(id_token_hint="id123", post_logout_redirect_uri="https://app.com/post_logout")
    assert "https://sso.staging.acesso.gov.br/logout?" in url
    assert "id_token_hint=id123" in url
    assert "post_logout_redirect_uri=https%3A%2F%2Fapp.com%2Fpost_logout" in url


def test_get_logout_url_default(client):
    url = client.get_logout_url()
    assert "https://sso.staging.acesso.gov.br/logout?" in url
    assert "post_logout_redirect_uri=https%3A%2F%2Fapp.com%2Fcallback" in url
