import pytest
from django.contrib.auth import get_user_model
from django.test import RequestFactory, override_settings

from django_govbr_auth.backends import GovBrAuthBackend, _filter_fields
from django_govbr_auth.exceptions import GovBrUserNotAllowedError

User = get_user_model()


@pytest.fixture
def backend():
    return GovBrAuthBackend()


@pytest.fixture
def rf():
    return RequestFactory()


@pytest.mark.django_db
def test_authenticate_none_user_info(backend, rf):
    request = rf.get("/")
    assert backend.authenticate(request, govbr_user_info=None) is None


@pytest.mark.django_db
def test_authenticate_missing_lookup_value(backend, rf):
    request = rf.get("/")
    info = {"name": "No Sub User", "email": "nosub@example.com"}
    assert backend.authenticate(request, govbr_user_info=info) is None


@pytest.mark.django_db
def test_authenticate_create_user_success(backend, rf):
    request = rf.get("/")
    info = {"sub": "11122233344", "name": "Ana Clara", "email": "ana@example.com"}
    user = backend.authenticate(request, govbr_user_info=info)
    assert user is not None
    assert user.username == "11122233344"
    assert user.first_name == "Ana"
    assert user.last_name == "Clara"
    assert user.email == "ana@example.com"
    assert user.is_active is True


@pytest.mark.django_db
def test_authenticate_user_json_field(backend, rf):
    with override_settings(
        GOVBR_AUTH={
            "CLIENT_ID": "id",
            "CLIENT_SECRET": "sec",
            "REDIRECT_URI": "https://example.com",
            "USER_JSON_FIELD": "first_name",
        }
    ):
        request = rf.get("/")
        info = {"sub": "99911122233"}
        user = backend.authenticate(request, govbr_user_info=info)
        assert user.first_name == info


@pytest.mark.django_db
def test_authenticate_first_user_defaults(backend, rf):
    with override_settings(
        GOVBR_AUTH={
            "CLIENT_ID": "id",
            "CLIENT_SECRET": "sec",
            "REDIRECT_URI": "https://example.com",
            "FIRST_USER_DEFAULTS": {"is_superuser": True, "is_staff": True},
        }
    ):
        request = rf.get("/")
        info = {"sub": "00000000000", "name": "Admin User"}
        user = backend.authenticate(request, govbr_user_info=info)
        assert user.is_superuser is True
        assert user.is_staff is True


@pytest.mark.django_db
def test_authenticate_create_user_disabled(backend, rf):
    with override_settings(
        GOVBR_AUTH={
            "CLIENT_ID": "id",
            "CLIENT_SECRET": "sec",
            "REDIRECT_URI": "https://example.com",
            "CREATE_USER": False,
        }
    ):
        request = rf.get("/")
        info = {"sub": "99988877766", "name": "Non Existent"}
        with pytest.raises(GovBrUserNotAllowedError) as exc_info:
            backend.authenticate(request, govbr_user_info=info)
        assert "CREATE_USER is disabled" in str(exc_info.value)


@pytest.mark.django_db
def test_authenticate_update_existing_user(backend, rf):
    existing_user = User.objects.create(
        username="12345678900",
        first_name="OldName",
        email="old@example.com",
        is_active=False,
    )

    request = rf.get("/")
    info = {"sub": "12345678900", "name": "NewName Silva", "email": "new@example.com"}

    updated_user = backend.authenticate(request, govbr_user_info=info)
    assert updated_user.pk == existing_user.pk
    assert updated_user.first_name == "NewName"
    assert updated_user.last_name == "Silva"
    assert updated_user.email == "new@example.com"
    assert updated_user.is_active is True


@pytest.mark.django_db
def test_authenticate_update_fields_restricted(backend, rf):
    User.objects.create(
        username="55544433322",
        first_name="FixedName",
        email="fixed@example.com",
    )

    with override_settings(
        GOVBR_AUTH={
            "CLIENT_ID": "id",
            "CLIENT_SECRET": "sec",
            "REDIRECT_URI": "https://example.com",
            "UPDATE_FIELDS_ON_LOGIN": [],
        }
    ):
        request = rf.get("/")
        info = {"sub": "55544433322", "name": "Changed Name", "email": "changed@example.com"}
        updated_user = backend.authenticate(request, govbr_user_info=info)
        assert updated_user.first_name == "FixedName"


@pytest.mark.django_db
def test_get_user(backend):
    user = User.objects.create(username="testuser")
    assert backend.get_user(user.pk) == user
    assert backend.get_user(999999) is None


def test_filter_fields():
    attrs = {"a": 1, "b": 2, "c": 3}
    assert _filter_fields(attrs, None) == attrs
    assert _filter_fields(attrs, []) == {}
    assert _filter_fields(attrs, ["a", "c"]) == {"a": 1, "c": 3}
