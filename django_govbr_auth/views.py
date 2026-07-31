import logging
from urllib.parse import urlsplit, urlunsplit

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.http import HttpResponseRedirect
from django.shortcuts import redirect
from django.utils.http import url_has_allowed_host_and_scheme
from django.views import View

from .exceptions import (
    GovBrAuthenticationError,
    GovBrStateMismatchError,
    GovBrTokenError,
    GovBrUserInfoError,
    GovBrUserNotAllowedError,
)
from .utils import generate_pkce_pair, generate_state, get_govbr_settings, get_oauth2_client

logger = logging.getLogger(__name__)


class GovBrLoginView(View):
    """
    Initiates the Gov.br OAuth2/OIDC authorization code flow with PKCE.

    If ``GOVBR_AUTH['DIRECT_REDIRECT']`` is ``True`` (the default), the user is
    redirected immediately to Gov.br SSO. Set it to ``False`` to render an
    intermediate confirmation page instead.
    """

    intermediate_template = "django_govbr_auth/login.html"

    def get(self, request):
        cfg = get_govbr_settings()
        if not cfg["direct_redirect"]:
            from django.shortcuts import render

            return render(request, self.intermediate_template)

        return self._redirect_to_govbr(request)

    def post(self, request):
        """Handle form submission from the intermediate login page."""
        return self._redirect_to_govbr(request)

    def _redirect_to_govbr(self, request):
        client = get_oauth2_client()
        state = generate_state()
        code_verifier, code_challenge = generate_pkce_pair()

        request.session["govbr_oauth2_state"] = state
        request.session["govbr_pkce_code_verifier"] = code_verifier

        authorization_url = client.get_authorization_url(state, code_challenge)
        return redirect(authorization_url)


class GovBrCallbackView(View):
    """Handles the OAuth2/OIDC callback from Gov.br SSO."""

    def get(self, request):
        cfg = get_govbr_settings()
        error = request.GET.get("error")
        if error:
            messages.error(request, f"Gov.br login error: {error}")
            return redirect(getattr(settings, "LOGIN_URL", "/accounts/login/"))

        try:
            # 1. Validate state (CSRF protection) and retrieve PKCE verifier
            received_state = request.GET.get("state", "")
            stored_state = request.session.pop("govbr_oauth2_state", None)
            code_verifier = request.session.pop("govbr_pkce_code_verifier", None)

            if not stored_state or received_state != stored_state or not code_verifier:
                raise GovBrStateMismatchError("OAuth2 state mismatch or missing PKCE verifier — possible CSRF attack.")

            # 2. Exchange code for access token & id_token
            code = request.GET.get("code")
            if not code:
                raise GovBrTokenError("No authorization code provided in callback.")

            client = get_oauth2_client()
            try:
                token_data = client.exchange_code_for_token(code, code_verifier)
            except Exception as e:
                raise GovBrTokenError(f"Failed to exchange code for token: {e}") from e

            access_token = token_data.get("access_token")
            if not access_token:
                raise GovBrTokenError("access_token not found in token response")

            id_token = token_data.get("id_token")
            if id_token:
                request.session["govbr_id_token"] = id_token

            # 3. Retrieve user profile info
            try:
                user_info = client.get_user_info(access_token)
            except Exception as e:
                raise GovBrUserInfoError(f"Failed to retrieve user info: {e}") from e

            # 4. Authenticate user in Django
            user = authenticate(request, govbr_user_info=user_info)

            if user is not None:
                login(request, user, backend=cfg["backend"])

                # 5. Redirect to safe next URL or LOGIN_REDIRECT_URL
                next_url = request.GET.get("next", "")
                safe_next_url = next_url.replace("\\", "")
                parsed_next = urlsplit(safe_next_url)
                is_safe = (
                    safe_next_url
                    and safe_next_url.startswith("/")
                    and not parsed_next.scheme
                    and not parsed_next.netloc
                    and url_has_allowed_host_and_scheme(
                        url=safe_next_url,
                        allowed_hosts={request.get_host()},
                        require_https=request.is_secure(),
                    )
                )

                if is_safe:
                    safe_redirect = urlunsplit(("", "", parsed_next.path, parsed_next.query, ""))
                    return HttpResponseRedirect(safe_redirect)

                login_redirect_url = getattr(settings, "LOGIN_REDIRECT_URL", "/")
                return redirect(login_redirect_url)
            else:
                raise GovBrAuthenticationError("Authentication failed. User not found or invalid credentials.")

        except GovBrStateMismatchError:
            messages.error(request, "Security check failed. Please try logging in again.")
            return redirect(getattr(settings, "LOGIN_URL", "/accounts/login/"))
        except GovBrTokenError:
            messages.error(request, "Failed to complete login. Please try again.")
            return redirect(getattr(settings, "LOGIN_URL", "/accounts/login/"))
        except GovBrUserInfoError:
            messages.error(request, "Failed to retrieve your profile. Please try again.")
            return redirect(getattr(settings, "LOGIN_URL", "/accounts/login/"))
        except GovBrUserNotAllowedError:
            messages.error(request, "Your account is not authorised to access this application.")
            return redirect(getattr(settings, "LOGIN_URL", "/accounts/login/"))
        except GovBrAuthenticationError:
            messages.error(request, "Authentication failed. Please try again.")
            return redirect(getattr(settings, "LOGIN_URL", "/accounts/login/"))
        except Exception:
            messages.error(request, "An unexpected error occurred. Please try again.")
            return redirect(getattr(settings, "LOGIN_URL", "/accounts/login/"))


class GovBrLogoutView(View):
    """
    Handles Single Sign-Out from Gov.br SSO.

    Logs the user out of Django and redirects to the Gov.br OIDC logout endpoint.
    """

    def get(self, request):
        cfg = get_govbr_settings()
        id_token = request.session.get("govbr_id_token")

        logout(request)

        client = get_oauth2_client()
        post_logout_uri = cfg["post_logout_redirect_uri"] or getattr(settings, "LOGOUT_REDIRECT_URL", None)
        logout_url = client.get_logout_url(id_token_hint=id_token, post_logout_redirect_uri=post_logout_uri)
        return redirect(logout_url)
