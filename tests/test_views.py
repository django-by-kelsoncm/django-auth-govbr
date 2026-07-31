from unittest.mock import MagicMock, patch

import pytest
from django.contrib.auth import get_user_model
from django.test import Client
from django.urls import reverse

from django_govbr_auth.exceptions import GovBrUserNotAllowedError

User = get_user_model()


@pytest.fixture
def django_client():
    return Client()


@pytest.mark.django_db
def test_login_view_direct_redirect(django_client):
    url = reverse("django_govbr_auth:login")
    response = django_client.get(url)
    assert response.status_code == 302
    assert "https://sso.staging.acesso.gov.br/authorize?" in response["Location"]
    assert "govbr_oauth2_state" in django_client.session
    assert "govbr_pkce_code_verifier" in django_client.session


@pytest.mark.django_db
def test_login_view_indirect_redirect(django_client, settings):
    settings.GOVBR_AUTH = {
        "CLIENT_ID": "id",
        "CLIENT_SECRET": "sec",
        "REDIRECT_URI": "https://example.com/callback/",
        "DIRECT_REDIRECT": False,
    }
    url = reverse("django_govbr_auth:login")
    response = django_client.get(url)
    assert response.status_code == 200
    assert "Autenticação Gov.br" in response.content.decode()

    post_resp = django_client.post(url)
    assert post_resp.status_code == 302
    assert "https://sso.staging.acesso.gov.br/authorize?" in post_resp["Location"]


@pytest.mark.django_db
def test_callback_error_query_param(django_client):
    url = reverse("django_govbr_auth:callback") + "?error=access_denied"
    response = django_client.get(url)
    assert response.status_code == 302
    assert response["Location"] == "/auth/govbr/login/"


@pytest.mark.django_db
def test_callback_state_mismatch(django_client):
    session = django_client.session
    session["govbr_oauth2_state"] = "valid_state"
    session["govbr_pkce_code_verifier"] = "verifier123"
    session.save()

    url = reverse("django_govbr_auth:callback") + "?state=wrong_state&code=code123"
    response = django_client.get(url)
    assert response.status_code == 302
    assert response["Location"] == "/auth/govbr/login/"


@pytest.mark.django_db
def test_callback_missing_code(django_client):
    session = django_client.session
    session["govbr_oauth2_state"] = "valid_state"
    session["govbr_pkce_code_verifier"] = "verifier123"
    session.save()

    url = reverse("django_govbr_auth:callback") + "?state=valid_state"
    response = django_client.get(url)
    assert response.status_code == 302
    assert response["Location"] == "/auth/govbr/login/"


@pytest.mark.django_db
@patch("django_govbr_auth.views.get_oauth2_client")
def test_callback_token_exchange_error(mock_get_client, django_client):
    mock_oauth = MagicMock()
    mock_oauth.exchange_code_for_token.side_effect = Exception("Token error")
    mock_get_client.return_value = mock_oauth

    session = django_client.session
    session["govbr_oauth2_state"] = "valid_state"
    session["govbr_pkce_code_verifier"] = "verifier123"
    session.save()

    url = reverse("django_govbr_auth:callback") + "?state=valid_state&code=code123"
    response = django_client.get(url)
    assert response.status_code == 302
    assert response["Location"] == "/auth/govbr/login/"


@pytest.mark.django_db
@patch("django_govbr_auth.views.get_oauth2_client")
def test_callback_missing_access_token(mock_get_client, django_client):
    mock_oauth = MagicMock()
    mock_oauth.exchange_code_for_token.return_value = {"id_token": "id123"}
    mock_get_client.return_value = mock_oauth

    session = django_client.session
    session["govbr_oauth2_state"] = "valid_state"
    session["govbr_pkce_code_verifier"] = "verifier123"
    session.save()

    url = reverse("django_govbr_auth:callback") + "?state=valid_state&code=code123"
    response = django_client.get(url)
    assert response.status_code == 302
    assert response["Location"] == "/auth/govbr/login/"


@pytest.mark.django_db
@patch("django_govbr_auth.views.get_oauth2_client")
def test_callback_user_info_error(mock_get_client, django_client):
    mock_oauth = MagicMock()
    mock_oauth.exchange_code_for_token.return_value = {"access_token": "token123"}
    mock_oauth.get_user_info.side_effect = Exception("UserInfo error")
    mock_get_client.return_value = mock_oauth

    session = django_client.session
    session["govbr_oauth2_state"] = "valid_state"
    session["govbr_pkce_code_verifier"] = "verifier123"
    session.save()

    url = reverse("django_govbr_auth:callback") + "?state=valid_state&code=code123"
    response = django_client.get(url)
    assert response.status_code == 302
    assert response["Location"] == "/auth/govbr/login/"


@pytest.mark.django_db
@patch("django_govbr_auth.views.get_oauth2_client")
@patch("django_govbr_auth.views.authenticate")
def test_callback_user_not_allowed_error(mock_auth, mock_get_client, django_client):
    mock_oauth = MagicMock()
    mock_oauth.exchange_code_for_token.return_value = {"access_token": "token123"}
    mock_oauth.get_user_info.return_value = {"sub": "99900011122"}
    mock_get_client.return_value = mock_oauth

    mock_auth.side_effect = GovBrUserNotAllowedError("User not allowed")

    session = django_client.session
    session["govbr_oauth2_state"] = "valid_state"
    session["govbr_pkce_code_verifier"] = "verifier123"
    session.save()

    url = reverse("django_govbr_auth:callback") + "?state=valid_state&code=code123"
    response = django_client.get(url)
    assert response.status_code == 302
    assert response["Location"] == "/auth/govbr/login/"


@pytest.mark.django_db
@patch("django_govbr_auth.views.get_oauth2_client")
@patch("django_govbr_auth.views.authenticate")
def test_callback_authentication_error(mock_auth, mock_get_client, django_client):
    mock_oauth = MagicMock()
    mock_oauth.exchange_code_for_token.return_value = {"access_token": "token123"}
    mock_oauth.get_user_info.return_value = {"sub": "12345678901"}
    mock_get_client.return_value = mock_oauth

    mock_auth.return_value = None

    session = django_client.session
    session["govbr_oauth2_state"] = "valid_state"
    session["govbr_pkce_code_verifier"] = "verifier123"
    session.save()

    url = reverse("django_govbr_auth:callback") + "?state=valid_state&code=code123"
    response = django_client.get(url)
    assert response.status_code == 302
    assert response["Location"] == "/auth/govbr/login/"


@pytest.mark.django_db
@patch("django_govbr_auth.views.get_oauth2_client")
@patch("django_govbr_auth.views.login")
@patch("django_govbr_auth.views.urlsplit")
def test_callback_unexpected_exception(mock_urlsplit, mock_login, mock_get_client, django_client):
    User.objects.create_user(username="12345678901")

    mock_oauth = MagicMock()
    mock_oauth.exchange_code_for_token.return_value = {"access_token": "token123"}
    mock_oauth.get_user_info.return_value = {"sub": "12345678901"}
    mock_get_client.return_value = mock_oauth

    mock_urlsplit.side_effect = RuntimeError("Unexpected system error")

    session = django_client.session
    session["govbr_oauth2_state"] = "valid_state"
    session["govbr_pkce_code_verifier"] = "verifier123"
    session.save()

    url = reverse("django_govbr_auth:callback") + "?state=valid_state&code=code123&next=/dashboard/"
    response = django_client.get(url)
    assert response.status_code == 302
    assert response["Location"] == "/auth/govbr/login/"


@pytest.mark.django_db
@patch("django_govbr_auth.views.get_oauth2_client")
@patch("django_govbr_auth.views.login")
def test_callback_success_and_safe_next(mock_login, mock_get_client, django_client):
    User.objects.create_user(username="12345678901", email="carlos@example.com")

    mock_oauth = MagicMock()
    mock_oauth.exchange_code_for_token.return_value = {"access_token": "token123", "id_token": "my_id_token"}
    mock_oauth.get_user_info.return_value = {"sub": "12345678901", "name": "Carlos Eduardo"}
    mock_get_client.return_value = mock_oauth

    session = django_client.session
    session["govbr_oauth2_state"] = "valid_state"
    session["govbr_pkce_code_verifier"] = "verifier123"
    session.save()

    url = reverse("django_govbr_auth:callback") + "?state=valid_state&code=code123&next=/dashboard/"
    response = django_client.get(url)
    assert response.status_code == 302
    assert response["Location"] == "/dashboard/"
    assert django_client.session["govbr_id_token"] == "my_id_token"
    mock_login.assert_called_once()


@pytest.mark.django_db
@patch("django_govbr_auth.views.get_oauth2_client")
@patch("django_govbr_auth.views.login")
def test_callback_success_unsafe_next_fallback(mock_login, mock_get_client, django_client):
    User.objects.create_user(username="12345678901")

    mock_oauth = MagicMock()
    mock_oauth.exchange_code_for_token.return_value = {"access_token": "token123"}
    mock_oauth.get_user_info.return_value = {"sub": "12345678901"}
    mock_get_client.return_value = mock_oauth

    session = django_client.session
    session["govbr_oauth2_state"] = "valid_state"
    session["govbr_pkce_code_verifier"] = "verifier123"
    session.save()

    url = reverse("django_govbr_auth:callback") + "?state=valid_state&code=code123&next=https://evil.com"
    response = django_client.get(url)
    assert response.status_code == 302
    assert response["Location"] == "/dashboard/"


@pytest.mark.django_db
def test_logout_view(django_client):
    session = django_client.session
    session["govbr_id_token"] = "sample_id_token"
    session.save()

    url = reverse("django_govbr_auth:logout")
    response = django_client.get(url)
    assert response.status_code == 302
    assert "https://sso.staging.acesso.gov.br/logout?" in response["Location"]
    assert "id_token_hint=sample_id_token" in response["Location"]
