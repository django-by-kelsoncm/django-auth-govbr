import logging
import secrets

from django.shortcuts import redirect, render
from django.views import View

from .exceptions import (
    GovBrAuthError,
    GovBrNonceMismatchError,
    GovBrProviderError,
    GovBrStateMismatchError,
    GovBrTokenError,
    GovBrUserInfoError,
)
from .handlers import get_login_handler, safe_next_url
from .utils import (
    decode_jwt_payload,
    generate_nonce,
    generate_pkce_pair,
    generate_state,
    get_govbr_settings,
    get_oauth2_client,
)

logger = logging.getLogger(__name__)

SESSION_STATE = "govbr_oauth2_state"
SESSION_VERIFIER = "govbr_pkce_code_verifier"
SESSION_NONCE = "govbr_oidc_nonce"
SESSION_NEXT = "govbr_next"
SESSION_ID_TOKEN = "govbr_id_token"


class GovBrLoginView(View):
    """
    Initiates the Gov.br OAuth2/OIDC authorization code flow with PKCE, ``state`` and ``nonce``.

    If ``GOVBR_AUTH['DIRECT_REDIRECT']`` is ``True`` (the default), the user is
    redirected immediately to Gov.br SSO. Set it to ``False`` to render an
    intermediate confirmation page instead.

    A safe local ``next`` parameter is kept in the session and used after the callback.
    """

    intermediate_template = "django_govbr_auth/login.html"

    def get(self, request):
        cfg = get_govbr_settings()
        if not cfg["direct_redirect"]:
            return render(request, self.intermediate_template, {"next": request.GET.get("next", "")})

        return self._redirect_to_govbr(request, cfg)

    def post(self, request):
        """Handle form submission from the intermediate login page."""
        return self._redirect_to_govbr(request, get_govbr_settings())

    def _redirect_to_govbr(self, request, cfg):
        client = get_oauth2_client()
        state = generate_state()
        code_verifier, code_challenge = generate_pkce_pair()
        nonce = generate_nonce() if cfg["use_nonce"] else None

        request.session[SESSION_STATE] = state
        request.session[SESSION_VERIFIER] = code_verifier
        request.session.pop(SESSION_NONCE, None)
        if nonce:
            request.session[SESSION_NONCE] = nonce
        next_url = safe_next_url(request, request.POST.get("next") or request.GET.get("next"))
        request.session.pop(SESSION_NEXT, None)
        if next_url:
            request.session[SESSION_NEXT] = next_url

        authorization_url = client.get_authorization_url(state, code_challenge, nonce=nonce)
        return redirect(authorization_url)


def _check_nonce(id_token, expected_nonce):
    """Compare the ``nonce`` claim of the ID token with the one stored in the session."""
    try:
        claims = decode_jwt_payload(id_token)
    except ValueError as exc:
        raise GovBrNonceMismatchError(f"Could not read the ID token: {exc}") from exc
    if not secrets.compare_digest(str(claims.get("nonce", "")), expected_nonce):
        raise GovBrNonceMismatchError("OIDC nonce mismatch — possible replay attack.")


class GovBrCallbackView(View):
    """Handles the OAuth2/OIDC callback from Gov.br SSO and delegates the local login to the login handler."""

    def get(self, request):
        cfg = get_govbr_settings()
        handler = get_login_handler(cfg)

        # Always consume the one-time values, whatever the outcome.
        stored_state = request.session.pop(SESSION_STATE, None)
        code_verifier = request.session.pop(SESSION_VERIFIER, None)
        expected_nonce = request.session.pop(SESSION_NONCE, None)
        next_url = request.session.pop(SESSION_NEXT, None) or request.GET.get("next")

        try:
            error = request.GET.get("error")
            if error:
                raise GovBrProviderError(error, request.GET.get("error_description"))

            # 1. Validate state (CSRF protection) and retrieve PKCE verifier
            received_state = request.GET.get("state", "")
            if not stored_state or not code_verifier or not secrets.compare_digest(received_state, stored_state):
                raise GovBrStateMismatchError("OAuth2 state mismatch or missing PKCE verifier — possible CSRF attack.")

            # 2. Exchange code for access token & id_token
            code = request.GET.get("code")
            if not code:
                raise GovBrTokenError("No authorization code provided in callback.")

            client = get_oauth2_client()
            try:
                token_data = client.exchange_code_for_token(code, code_verifier)
            except GovBrTokenError:
                raise
            except Exception as e:
                raise GovBrTokenError(f"Failed to exchange code for token: {e}") from e

            access_token = token_data.get("access_token")
            if not access_token:
                raise GovBrTokenError("access_token not found in token response")

            # 3. Check the nonce (when one was sent) against the ID token
            id_token = token_data.get("id_token")
            if expected_nonce:
                if not id_token:
                    raise GovBrNonceMismatchError("id_token missing from token response; cannot check the nonce.")
                _check_nonce(id_token, expected_nonce)

            # 4. Retrieve user profile info
            try:
                user_info = client.get_user_info(access_token)
            except GovBrUserInfoError:
                raise
            except Exception as e:
                raise GovBrUserInfoError(f"Failed to retrieve user info: {e}") from e

            # 5. Local login, by the configured handler
            response = handler.login(request, user_info, token_data, next_url=next_url)
            if id_token:
                request.session[SESSION_ID_TOKEN] = id_token
            return response

        except GovBrAuthError as exc:
            logger.warning("Gov.br login failed: %s", exc)
            return handler.error(request, exc)
        except Exception as exc:
            logger.exception("Unexpected error in the Gov.br callback")
            return handler.error(request, exc)


class GovBrLogoutView(View):
    """
    Handles Single Sign-Out from Gov.br SSO.

    Ends the local session (``LOGIN_HANDLER.logout``) and redirects to the Gov.br OIDC logout endpoint.
    """

    def get(self, request):
        from django.conf import settings

        cfg = get_govbr_settings()
        id_token = request.session.get(SESSION_ID_TOKEN)

        get_login_handler(cfg).logout(request)

        client = get_oauth2_client()
        post_logout_uri = cfg["post_logout_redirect_uri"] or getattr(settings, "LOGOUT_REDIRECT_URL", None)
        logout_url = client.get_logout_url(id_token_hint=id_token, post_logout_redirect_uri=post_logout_uri)
        return redirect(logout_url)
