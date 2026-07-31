import base64
import hashlib

import pytest
from django.core.exceptions import ImproperlyConfigured
from django.test import override_settings

from django_govbr_auth.utils import (
    DEFAULT_USER_ATTR_MAP,
    PRODUCTION_BASE_URL,
    STAGING_BASE_URL,
    apply_user_attr_map,
    generate_pkce_pair,
    generate_state,
    get_govbr_settings,
    get_oauth2_client,
)


def test_get_govbr_settings_default(settings):
    cfg = get_govbr_settings()
    assert cfg["client_id"] == "test-client-id"
    assert cfg["client_secret"] == "test-client-secret"
    assert cfg["redirect_uri"] == "https://example.com/auth/govbr/callback/"
    assert cfg["environment"] == "staging"
    assert cfg["base_url"] == STAGING_BASE_URL
    assert cfg["scopes"] == ["openid", "email", "profile"]
    assert cfg["user_lookup_field"] == "username"
    assert cfg["user_attr_map"] == DEFAULT_USER_ATTR_MAP
    assert cfg["direct_redirect"] is True


def test_get_govbr_settings_production():
    with override_settings(
        GOVBR_AUTH={
            "CLIENT_ID": "id",
            "CLIENT_SECRET": "sec",
            "REDIRECT_URI": "https://example.com",
            "ENVIRONMENT": "production",
        }
    ):
        cfg = get_govbr_settings()
        assert cfg["environment"] == "production"
        assert cfg["base_url"] == PRODUCTION_BASE_URL


def test_get_govbr_settings_custom_base_url():
    with override_settings(
        GOVBR_AUTH={
            "CLIENT_ID": "id",
            "CLIENT_SECRET": "sec",
            "REDIRECT_URI": "https://example.com",
            "BASE_URL": "https://custom.gov.br",
        }
    ):
        cfg = get_govbr_settings()
        assert cfg["base_url"] == "https://custom.gov.br"


def test_get_govbr_settings_missing_required():
    with override_settings(GOVBR_AUTH={}):
        with pytest.raises(ImproperlyConfigured) as exc_info:
            get_govbr_settings()
        assert "CLIENT_ID" in str(exc_info.value)


def test_apply_user_attr_map():
    info = {
        "sub": "12345678901",
        "email": "user@example.com",
        "name": "Maria Silva Santos",
        "extra": {"confiabilidade": "ouro"},
    }
    attr_map = {
        "username": "sub",
        "email": "email",
        ("first_name", "last_name"): "name",
        "nivel": "extra.confiabilidade",
        "raw": "fulljson",
        "non_existent": "missing_key",
        "invalid_nest": "email.sub",
    }
    res = apply_user_attr_map(info, attr_map)
    assert res["username"] == "12345678901"
    assert res["email"] == "user@example.com"
    assert res["first_name"] == "Maria"
    assert res["last_name"] == "Silva Santos"
    assert res["nivel"] == "ouro"
    assert res["raw"] == info
    assert "non_existent" not in res
    assert "invalid_nest" not in res


def test_apply_user_attr_map_single_name():
    info = {"name": "Maria"}
    attr_map = {("first_name", "last_name"): "name"}
    res = apply_user_attr_map(info, attr_map)
    assert res["first_name"] == "Maria"
    assert res["last_name"] == ""


def test_generate_state():
    state1 = generate_state()
    state2 = generate_state()
    assert len(state1) > 20
    assert state1 != state2


def test_generate_pkce_pair():
    verifier, challenge = generate_pkce_pair()
    assert len(verifier) >= 43
    hashed = hashlib.sha256(verifier.encode("ascii")).digest()
    expected_challenge = base64.urlsafe_b64encode(hashed).decode("ascii").rstrip("=")
    assert challenge == expected_challenge


def test_get_oauth2_client():
    client = get_oauth2_client()
    assert client.client_id == "test-client-id"
    assert client.base_url == STAGING_BASE_URL
