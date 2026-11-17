"""Login handlers: what the callback does once Gov.br has identified the user.

The callback view validates ``state``/``nonce``, exchanges the code and fetches the profile; then it hands
``user_info`` and ``token_data`` to the handler configured in ``GOVBR_AUTH['LOGIN_HANDLER']``.

* :class:`DjangoAuthLoginHandler` (default) authenticates against ``AUTHENTICATION_BACKENDS`` and opens a
  ``django.contrib.auth`` session.
* Subclass :class:`BaseLoginHandler` for projects without ``django.contrib.auth`` (e.g. accounts kept by an API):
  implement :meth:`~BaseLoginHandler.login` and, if needed, :meth:`~BaseLoginHandler.logout` and
  :meth:`~BaseLoginHandler.error`.
"""

import inspect
from urllib.parse import urlsplit, urlunsplit

from django.conf import settings
from django.contrib import messages
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect
from django.shortcuts import redirect, resolve_url
from django.utils.http import url_has_allowed_host_and_scheme
from django.utils.module_loading import import_string
from django.utils.translation import gettext_lazy as _

from .exceptions import (
    GovBrAuthenticationError,
    GovBrProviderError,
    GovBrStateMismatchError,
    GovBrTokenError,
    GovBrUserInfoError,
    GovBrUserNotAllowedError,
)

# Most specific first: GovBrNonceMismatchError is a GovBrStateMismatchError.
ERROR_MESSAGES = (
    (GovBrProviderError, _("The Gov.br login was cancelled or refused. Please try again.")),
    (GovBrStateMismatchError, _("Security check failed. Please try logging in again.")),
    (GovBrTokenError, _("Failed to complete login. Please try again.")),
    (GovBrUserInfoError, _("Failed to retrieve your profile. Please try again.")),
    (GovBrUserNotAllowedError, _("Your account is not authorised to access this application.")),
    (GovBrAuthenticationError, _("Authentication failed. Please try again.")),
)
UNEXPECTED_ERROR_MESSAGE = _("An unexpected error occurred. Please try again.")


def safe_next_url(request: HttpRequest, next_url: str | None) -> str | None:
    """Return *next_url* reduced to a local path (+ query) when it is safe to redirect to, else ``None``."""
    candidate = (next_url or "").replace("\\", "")
    parsed = urlsplit(candidate)
    if (
        candidate.startswith("/")
        and not parsed.scheme
        and not parsed.netloc
        and url_has_allowed_host_and_scheme(
            url=candidate, allowed_hosts={request.get_host()}, require_https=request.is_secure()
        )
    ):
        return urlunsplit(("", "", parsed.path, parsed.query, ""))
    return None


class BaseLoginHandler:
    """Base class for login handlers. Subclasses must implement :meth:`login`."""

    def __init__(self, govbr_settings: dict | None = None):
        self.govbr_settings = govbr_settings or {}

    def login(
        self, request: HttpRequest, user_info: dict, token_data: dict, next_url: str | None = None
    ) -> HttpResponse:
        """Open the local session for the Gov.br user and return the response (usually a redirect).

        Raise a :class:`~django_govbr_auth.exceptions.GovBrAuthError` subclass to refuse the login; the view
        turns it into :meth:`error`.
        """
        raise NotImplementedError("Login handlers must implement login()")

    def logout(self, request: HttpRequest) -> None:
        """End the local session before the federated logout at Gov.br."""
        request.session.flush()

    def error(self, request: HttpRequest, exc: Exception) -> HttpResponse:
        """Return the response for a failed login. Default: flash message and redirect to ``LOGIN_URL``."""
        messages.error(request, self.get_error_message(exc), fail_silently=True)
        return redirect(getattr(settings, "LOGIN_URL", "/accounts/login/"))

    def get_error_message(self, exc: Exception):
        for exc_class, message in ERROR_MESSAGES:
            if isinstance(exc, exc_class):
                return message
        return UNEXPECTED_ERROR_MESSAGE

    def get_success_url(self, request: HttpRequest, next_url: str | None = None) -> str:
        return safe_next_url(request, next_url) or resolve_url(getattr(settings, "LOGIN_REDIRECT_URL", "/"))


class DjangoAuthLoginHandler(BaseLoginHandler):
    """Default handler: ``authenticate()`` with ``govbr_user_info`` and ``login()`` from ``django.contrib.auth``."""

    def login(self, request, user_info, token_data, next_url=None):
        from django.contrib.auth import authenticate, login

        user = authenticate(request, govbr_user_info=user_info)
        if user is None:
            raise GovBrAuthenticationError("Authentication failed. User not found or invalid credentials.")
        login(request, user, backend=self.govbr_settings.get("backend"))
        return HttpResponseRedirect(self.get_success_url(request, next_url))

    def logout(self, request):
        from django.contrib.auth import logout

        logout(request)


def get_login_handler(cfg: dict) -> BaseLoginHandler:
    """Instantiate the handler named in ``cfg['login_handler']`` (class, instance or import path)."""
    target = cfg["login_handler"]
    if isinstance(target, str):
        target = import_string(target)
    if inspect.isclass(target):
        return target(govbr_settings=cfg)
    return target
