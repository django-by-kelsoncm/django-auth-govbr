class GovBrAuthError(Exception):
    """Base exception for all django-auth-govbr errors."""

    pass


class GovBrStateMismatchError(GovBrAuthError):
    """Raised when the OAuth2 state parameter does not match the stored state (CSRF protection)."""

    pass


class GovBrTokenError(GovBrAuthError):
    """Raised when exchanging an authorization code for an access token fails."""

    pass


class GovBrUserInfoError(GovBrAuthError):
    """Raised when fetching the authenticated user's profile from Gov.br fails."""

    pass


class GovBrUserNotAllowedError(GovBrAuthError):
    """Raised when CREATE_USER is False and no local user exists for the Gov.br user."""

    pass


class GovBrAuthenticationError(GovBrAuthError):
    """Raised when user authentication or creation fails during the callback flow."""

    pass


class GovBrNonceMismatchError(GovBrStateMismatchError):
    """Raised when the ``nonce`` claim of the ID token does not match the one sent in the authorization request."""

    pass


class GovBrProviderError(GovBrAuthError):
    """Raised when Gov.br redirects back with an ``error`` parameter (e.g. the user cancelled the login)."""

    def __init__(self, error, description=None):
        self.error = error
        self.description = description
        super().__init__(f"Gov.br returned error '{error}'" + (f": {description}" if description else ""))
