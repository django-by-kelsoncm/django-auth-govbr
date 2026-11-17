"""Branches of fetchers, mappers, transformers and utils not exercised by the other test modules."""

from unittest.mock import MagicMock, patch

import pytest

from django_govbr_auth import fetchers, mappers, transformers, utils


def test_fetchers_resolve_invalid_target():
    with pytest.raises(TypeError):
        fetchers.resolve_callable_or_class(123)


def test_base_fetcher_returns_empty_dict():
    assert fetchers.BaseUserInfoFetcher().fetch(None, "t") == {}


def test_default_fetcher_dict_specs():
    client = MagicMock()
    client.get_endpoint_data.side_effect = lambda token, path: {
        "/lista": {"itens": [1, 2], "outro": 0},
        "/plano": {"a": 1},
        "/escalar": "texto",
    }[path]
    endpoints = [
        {"namespace": "sem_endpoint"},
        {"endpoint": "/lista", "namespace": "lista", "extract_list": "itens"},
        {"endpoint": "/plano"},
        {"endpoint": "/escalar"},
    ]
    fetcher = fetchers.DefaultEndpointsUserInfoFetcher({"user_info_endpoints": endpoints})
    assert fetcher.fetch(client, "t") == {"lista": [1, 2], "a": 1}


def test_fetcher_chain_accepts_plain_callables():
    def fetcher(client, token, info):
        return {**info, "chamado": True}

    cfg = {"user_info_fetchers": [fetcher, "django_govbr_auth.fetchers.BaseUserInfoFetcher"]}
    assert fetchers.run_user_info_fetcher_chain(None, "t", cfg) == {"chamado": True}


def test_fetcher_chain_reads_settings_by_default():
    with patch.object(fetchers.DefaultEndpointsUserInfoFetcher, "fetch", return_value={"sub": "1"}):
        assert fetchers.run_user_info_fetcher_chain(None, "t") == {"sub": "1"}


def test_extract_nested_invalid_key():
    assert mappers._extract_nested({"a": 1}, None) is None
    assert utils._extract_nested({"a": {"b": 2}}, "a.b") == 2


def test_call_transformer_signatures():
    def dois_com_extra(v, info=None, extra=None):
        return (v, info)

    def so_valor(v, *, a=None, b=None):  # three parameters, but only one positional
        return v

    assert mappers._call_transformer(dois_com_extra, 1, 2) == (1, 2)
    assert mappers._call_transformer(so_valor, 1, 2) == 1


def test_base_mapper_returns_empty_dict():
    assert mappers.BaseUserMapper().map_attributes({}) == {}


def test_dict_spec_without_value_and_transform_is_skipped():
    mapper = mappers.DefaultAttrMapUserMapper({"user_attr_map": {"x": {"key": "ausente"}, "y": 123}})
    assert mapper.map_attributes({}) == {}


def test_mapper_chain_accepts_plain_callables_and_settings_default():
    def mapper(info, attrs):
        return {**attrs, "chamado": True}

    assert mappers.run_user_info_mapper_chain({}, cfg={"user_info_mappers": [mapper]}) == {"chamado": True}
    assert mappers.get_user_info_mappers()[0].__class__ is mappers.DefaultAttrMapUserMapper
    assert mappers.run_user_info_mapper_chain({"sub": "1"})["username"] == "1"


def test_to_bool_other_types():
    assert transformers.to_bool(None) is False
    assert transformers.to_bool([1]) is True


def test_fetch_image_file_name_without_extension():
    response = MagicMock(content=b"img")
    with patch("requests.get", return_value=response):
        assert transformers.fetch_image_file("https://x/foto").name == "foto.jpg"
        assert transformers.fetch_image_file("https://x/").name == "govbr_photo.jpg"
    assert transformers.fetch_image_file(None) is None


def test_get_endpoint_data_with_full_url():
    from django_govbr_auth.client import GovBrOAuth2Client

    client = GovBrOAuth2Client("id", "s", "https://app/cb/")
    with patch.object(client._session, "get", return_value=MagicMock(json=lambda: {"ok": 1})) as get:
        assert client.get_endpoint_data("t", "https://api.staging.acesso.gov.br/x") == {"ok": 1}
    assert get.call_args.args[0] == "https://api.staging.acesso.gov.br/x"


def test_legacy_user_mapper_setting(settings):
    settings.GOVBR_AUTH = {**settings.GOVBR_AUTH, "USER_MAPPER": "django_govbr_auth.mappers.BaseUserMapper"}
    assert utils.get_govbr_settings()["user_info_mappers"] == ["django_govbr_auth.mappers.BaseUserMapper"]
