from django_govbr_auth.exceptions import (
    GovBrAuthenticationError,
    GovBrAuthError,
    GovBrStateMismatchError,
    GovBrTokenError,
    GovBrUserInfoError,
    GovBrUserNotAllowedError,
)


def test_exception_inheritance():
    assert issubclass(GovBrStateMismatchError, GovBrAuthError)
    assert issubclass(GovBrTokenError, GovBrAuthError)
    assert issubclass(GovBrUserInfoError, GovBrAuthError)
    assert issubclass(GovBrUserNotAllowedError, GovBrAuthError)
    assert issubclass(GovBrAuthenticationError, GovBrAuthError)
