import base64
import json
from unittest.mock import MagicMock, patch
from urllib.parse import parse_qs, urlsplit

import pytest
import responses
from django.http import HttpResponse, HttpResponseRedirect
from django.test import Client
from django.urls import reverse

from django_govbr_auth.client import GovBrOAuth2Client
from django_govbr_auth.exceptions import (
    GovBrNonceMismatchError,
    GovBrProviderError,
    GovBrStateMismatchError,
    GovBrTokenError,
    GovBrUserInfoError,
)
from django_govbr_auth.handlers import (
    BaseLoginHandler,
    DjangoAuthLoginHandler,
    get_login_handler,
    safe_next_url,
)
from django_govbr_auth.utils import decode_jwt_payload, get_govbr_settings

CALLBACK = "django_govbr_auth:callback"


def jwt(claims):
    def part(data):
        return base64.urlsafe_b64encode(json.dumps(data).encode()).rstrip(b"=").decode()

    return f"{part({'alg': 'RS256'})}.{part(claims)}.assinatura"


class SessionOnlyHandler(BaseLoginHandler):
    """A handler for projects without django.contrib.auth: keeps the Gov.br user in the session."""

    def login(self, request, user_info, token_data, next_url=None):
        request.session.cycle_key()
        request.session["usuario"] = user_info["sub"]
        return HttpResponseRedirect(self.get_success_url(request, next_url))

    def error(self, request, exc):
        return HttpResponse(f"erro: {type(exc).__name__}", status=400)


@pytest.fixture
def django_client():
    return Client()


@pytest.fixture
def session_only(settings):
    settings.GOVBR_AUTH = {**settings.GOVBR_AUTH, "LOGIN_HANDLER": SessionOnlyHandler}


def start_login(django_client, next_url=None):
    url = reverse("django_govbr_auth:login") + (f"?next={next_url}" if next_url else "")
    response = django_client.get(url)
    params = parse_qs(urlsplit(response["Location"]).query)
    return params["state"][0], params.get("nonce", [None])[0]


def callback(django_client, query, oauth):
    with patch("django_govbr_auth.views.get_oauth2_client", return_value=oauth):
        return django_client.get(reverse(CALLBACK) + query)


def mock_client(id_token=None, user_info=None):
    oauth = MagicMock()
    token = {"access_token": "token123"}
    if id_token:
        token["id_token"] = id_token
    oauth.exchange_code_for_token.return_value = token
    oauth.get_user_info.return_value = user_info or {"sub": "12345678901"}
    return oauth


# ---------------------------------------------------------------- nonce


@pytest.mark.django_db
def test_login_sends_nonce_and_keeps_it_in_session(django_client):
    state, nonce = start_login(django_client)
    assert nonce
    assert django_client.session["govbr_oidc_nonce"] == nonce


@pytest.mark.django_db
def test_login_without_nonce_when_disabled(django_client, settings):
    settings.GOVBR_AUTH = {**settings.GOVBR_AUTH, "USE_NONCE": False}
    _, nonce = start_login(django_client)
    assert nonce is None
    assert "govbr_oidc_nonce" not in django_client.session


@pytest.mark.django_db
@pytest.mark.usefixtures("session_only")
def test_callback_accepts_matching_nonce(django_client):
    state, nonce = start_login(django_client)
    response = callback(django_client, f"?state={state}&code=c", mock_client(id_token=jwt({"nonce": nonce})))

    assert response.status_code == 302
    assert django_client.session["usuario"] == "12345678901"
    assert "govbr_oidc_nonce" not in django_client.session


@pytest.mark.django_db
@pytest.mark.usefixtures("session_only")
@pytest.mark.parametrize("id_token", [None, "nao-e-jwt", jwt({"nonce": "outro"}), jwt({})])
def test_callback_rejects_bad_nonce(django_client, id_token):
    state, _ = start_login(django_client)
    response = callback(django_client, f"?state={state}&code=c", mock_client(id_token=id_token))

    assert response.status_code == 400
    assert response.content == b"erro: GovBrNonceMismatchError"
    assert "usuario" not in django_client.session


def test_nonce_error_is_a_state_error():
    assert issubclass(GovBrNonceMismatchError, GovBrStateMismatchError)


def test_decode_jwt_payload():
    assert decode_jwt_payload(jwt({"nonce": "n", "sub": "1"})) == {"nonce": "n", "sub": "1"}
    for invalid in ("x", "a.b.c", None, f"a.{base64.urlsafe_b64encode(b'[1]').decode()}.c"):
        with pytest.raises(ValueError):
            decode_jwt_payload(invalid)


# ---------------------------------------------------------------- custom handler (no django.contrib.auth)


@pytest.mark.django_db
@pytest.mark.usefixtures("session_only")
def test_custom_handler_uses_next_kept_in_session(django_client):
    state, nonce = start_login(django_client, next_url="/painel/?aba=2")
    response = callback(django_client, f"?state={state}&code=c", mock_client(id_token=jwt({"nonce": nonce})))

    assert response["Location"] == "/painel/?aba=2"
    assert django_client.session["govbr_id_token"]


@pytest.mark.django_db
@pytest.mark.usefixtures("session_only")
def test_unsafe_next_is_not_kept(django_client):
    start_login(django_client, next_url="https://evil.com/")
    assert "govbr_next" not in django_client.session


@pytest.mark.django_db
@pytest.mark.usefixtures("session_only")
@pytest.mark.parametrize(
    "query, erro",
    [
        ("?error=access_denied&error_description=cancelado", "GovBrProviderError"),
        ("?state=errado&code=c", "GovBrStateMismatchError"),
    ],
)
def test_custom_handler_receives_errors(django_client, query, erro):
    start_login(django_client)
    response = django_client.get(reverse(CALLBACK) + query)
    assert response.content == f"erro: {erro}".encode()
    # one-time values are consumed even on failure
    assert "govbr_oauth2_state" not in django_client.session


@pytest.mark.django_db
@pytest.mark.usefixtures("session_only")
def test_custom_handler_receives_user_info_errors(django_client):
    state, nonce = start_login(django_client)
    oauth = mock_client(id_token=jwt({"nonce": nonce}))
    oauth.get_user_info.side_effect = GovBrUserInfoError("falhou")
    response = callback(django_client, f"?state={state}&code=c", oauth)
    assert response.content == b"erro: GovBrUserInfoError"


@pytest.mark.django_db
@pytest.mark.usefixtures("session_only")
@pytest.mark.parametrize("falha", ["token", "token_govbr", "userinfo", "inesperada"])
def test_unexpected_client_errors_are_wrapped(django_client, falha):
    state, nonce = start_login(django_client)
    oauth = mock_client(id_token=jwt({"nonce": nonce}))
    if falha == "token":
        oauth.exchange_code_for_token.side_effect = RuntimeError("x")
    elif falha == "token_govbr":
        oauth.exchange_code_for_token.side_effect = GovBrTokenError("x")
    else:
        oauth.get_user_info.side_effect = RuntimeError("x")
    if falha == "inesperada":
        oauth.get_user_info.side_effect = None
        oauth.get_user_info.return_value = {}  # SessionOnlyHandler.login fails with KeyError
    response = callback(django_client, f"?state={state}&code=c", oauth)
    esperado = {
        "token": "GovBrTokenError",
        "token_govbr": "GovBrTokenError",
        "userinfo": "GovBrUserInfoError",
        "inesperada": "KeyError",
    }[falha]
    assert response.content == f"erro: {esperado}".encode()


@pytest.mark.django_db
def test_intermediate_page_keeps_next(django_client, settings):
    settings.GOVBR_AUTH = {**settings.GOVBR_AUTH, "DIRECT_REDIRECT": False}
    url = reverse("django_govbr_auth:login")
    assert 'name="next" value="/painel/"' in django_client.get(url + "?next=/painel/").content.decode()
    django_client.post(url, {"next": "/painel/"})
    assert django_client.session["govbr_next"] == "/painel/"


@pytest.mark.django_db
@pytest.mark.usefixtures("session_only")
def test_logout_uses_handler(django_client):
    session = django_client.session
    session["usuario"] = "12345678901"
    session["govbr_id_token"] = "id123"
    session.save()

    response = django_client.get(reverse("django_govbr_auth:logout"))

    assert "id_token_hint=id123" in response["Location"]
    assert "usuario" not in django_client.session


def test_base_handler_login_is_abstract(rf):
    with pytest.raises(NotImplementedError):
        BaseLoginHandler().login(rf.get("/"), {}, {})


def test_get_login_handler_accepts_path_class_and_instance(settings):
    cfg = get_govbr_settings()
    assert isinstance(get_login_handler(cfg), DjangoAuthLoginHandler)
    assert isinstance(get_login_handler({**cfg, "login_handler": SessionOnlyHandler}), SessionOnlyHandler)
    instance = SessionOnlyHandler()
    assert get_login_handler({**cfg, "login_handler": instance}) is instance


def test_error_messages():
    handler = BaseLoginHandler()
    assert "cancelled" in str(handler.get_error_message(GovBrProviderError("access_denied")))
    assert "Security" in str(handler.get_error_message(GovBrNonceMismatchError("x")))
    assert "unexpected" in str(handler.get_error_message(RuntimeError("x")))


def test_provider_error_message():
    assert str(GovBrProviderError("access_denied", "cancelado")) == "Gov.br returned error 'access_denied': cancelado"
    assert GovBrProviderError("access_denied").description is None


def test_safe_next_url(rf):
    request = rf.get("/")
    assert safe_next_url(request, "/a/?b=1#frag") == "/a/?b=1"
    for unsafe in (None, "", "https://evil.com/", "//evil.com", "/\\evil.com", "relativo"):
        assert safe_next_url(request, unsafe) in (None, "/evil.com")


# ---------------------------------------------------------------- token endpoint authentication


@responses.activate
@pytest.mark.parametrize("method", ["client_secret_basic", "client_secret_post"])
def test_token_auth_method(method):
    responses.add(responses.POST, "https://sso.staging.acesso.gov.br/token", json={"access_token": "t"})
    client = GovBrOAuth2Client("meu-id", "meu-segredo", "https://app/cb/", token_auth_method=method)

    client.exchange_code_for_token("code", "verifier")

    request = responses.calls[0].request
    body = parse_qs(request.body)
    if method == "client_secret_basic":
        expected = "Basic " + base64.b64encode(b"meu-id:meu-segredo").decode()
        assert request.headers["Authorization"] == expected
        assert "client_secret" not in body
    else:
        assert "Authorization" not in request.headers
        assert body["client_secret"] == ["meu-segredo"]


def test_invalid_token_auth_method():
    with pytest.raises(ValueError):
        GovBrOAuth2Client("id", "s", "https://app/cb/", token_auth_method="private_key_jwt")


def test_authorization_url_with_nonce():
    client = GovBrOAuth2Client("id", "s", "https://app/cb/")
    assert "nonce=abc" in client.get_authorization_url("st", "ch", nonce="abc")
    assert "nonce" not in client.get_authorization_url("st", "ch")


# ---------------------------------------------------------------- required endpoints


@responses.activate
def test_optional_endpoint_failure_is_ignored(settings):
    settings.GOVBR_AUTH = {
        **settings.GOVBR_AUTH,
        "USER_INFO_ENDPOINTS": ["/userinfo", {"endpoint": "/extra", "namespace": "extra"}],
    }
    responses.add(responses.GET, "https://sso.staging.acesso.gov.br/userinfo", json={"sub": "1"})
    responses.add(responses.GET, "https://sso.staging.acesso.gov.br/extra", status=500)

    client = GovBrOAuth2Client("id", "s", "https://app/cb/")
    assert client.get_user_info("token") == {"sub": "1"}


@responses.activate
def test_endpoint_marked_required_raises(settings):
    settings.GOVBR_AUTH = {
        **settings.GOVBR_AUTH,
        "USER_INFO_ENDPOINTS": ["/userinfo", {"endpoint": "/extra", "required": True}],
    }
    responses.add(responses.GET, "https://sso.staging.acesso.gov.br/userinfo", json={"sub": "1"})
    responses.add(responses.GET, "https://sso.staging.acesso.gov.br/extra", status=500)

    client = GovBrOAuth2Client("id", "s", "https://app/cb/")
    with pytest.raises(GovBrUserInfoError):
        client.get_user_info("token")
