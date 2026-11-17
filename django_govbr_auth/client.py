from urllib.parse import urlencode

import requests

from .exceptions import GovBrTokenError, GovBrUserInfoError

DEFAULT_BASE_URL = "https://sso.staging.acesso.gov.br"

AUTHORIZE_PATH = "/authorize"
TOKEN_PATH = "/token"
USER_INFO_PATH = "/userinfo"
LOGOUT_PATH = "/logout"

CLIENT_SECRET_BASIC = "client_secret_basic"
CLIENT_SECRET_POST = "client_secret_post"
TOKEN_AUTH_METHODS = (CLIENT_SECRET_BASIC, CLIENT_SECRET_POST)


class GovBrOAuth2Client:
    """Handles the OIDC / OAuth2 authorization code flow with Gov.br (including PKCE)."""

    def __init__(
        self,
        client_id,
        client_secret,
        redirect_uri,
        scopes=None,
        base_url=None,
        token_auth_method=CLIENT_SECRET_BASIC,
    ):
        if token_auth_method not in TOKEN_AUTH_METHODS:
            raise ValueError(f"token_auth_method must be one of {TOKEN_AUTH_METHODS}, got {token_auth_method!r}")
        self.token_auth_method = token_auth_method
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.scopes = scopes or ["openid", "email", "profile"]
        self.base_url = (base_url or DEFAULT_BASE_URL).rstrip("/")
        self._session = requests.Session()

    def get_authorization_url(self, state, code_challenge, nonce=None):
        """Return the full authorization URL to redirect the user to Gov.br SSO."""
        params = {
            "response_type": "code",
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "scope": " ".join(self.scopes),
            "state": state,
            "code_challenge": code_challenge,
            "code_challenge_method": "S256",
        }
        if nonce:
            params["nonce"] = nonce
        return f"{self.base_url}{AUTHORIZE_PATH}?{urlencode(params)}"

    def exchange_code_for_token(self, code, code_verifier, timeout=30):
        """Exchange an authorization code and code_verifier for access/ID tokens.

        The client authenticates with HTTP Basic (``client_secret_basic``, as the Login Único technical guide
        documents) or, for compatibility, with the credentials in the form body (``client_secret_post``).
        """
        url = f"{self.base_url}{TOKEN_PATH}"
        data = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": self.redirect_uri,
            "code_verifier": code_verifier,
        }
        auth = None
        if self.token_auth_method == CLIENT_SECRET_BASIC:
            auth = (self.client_id, self.client_secret)
        else:
            data["client_id"] = self.client_id
            data["client_secret"] = self.client_secret
        try:
            response = self._session.post(url, data=data, auth=auth, timeout=timeout)
            response.raise_for_status()
            return response.json()
        except requests.HTTPError as exc:
            raise GovBrTokenError(f"Token exchange failed: {exc}") from exc
        except requests.RequestException as exc:
            raise GovBrTokenError(f"Token exchange request error: {exc}") from exc
        except Exception as exc:
            raise GovBrTokenError(f"Token exchange unexpected error: {exc}") from exc

    def get_endpoint_data(self, access_token, path_or_url, timeout=30):
        """Fetch JSON data from a specific Gov.br API endpoint or full URL."""
        if path_or_url.startswith("http://") or path_or_url.startswith("https://"):
            url = path_or_url
        else:
            url = f"{self.base_url}/{path_or_url.lstrip('/')}"
        headers = {"Authorization": f"Bearer {access_token}"}
        try:
            response = self._session.get(url, headers=headers, timeout=timeout)
            response.raise_for_status()
            return response.json()
        except requests.HTTPError as exc:
            raise GovBrUserInfoError(f"Failed to fetch endpoint '{path_or_url}': {exc}") from exc
        except requests.RequestException as exc:
            raise GovBrUserInfoError(f"Endpoint '{path_or_url}' request error: {exc}") from exc
        except Exception as exc:
            raise GovBrUserInfoError(f"Endpoint '{path_or_url}' unexpected error: {exc}") from exc

    def get_user_info(self, access_token, timeout=30):
        """Fetch the authenticated user's profile from Gov.br SSO via the fetcher chain."""
        from .fetchers import run_user_info_fetcher_chain

        return run_user_info_fetcher_chain(self, access_token)

    def get_logout_url(self, id_token_hint=None, post_logout_redirect_uri=None):
        """Return the OIDC Single Sign-Out URL for Gov.br."""
        params = {}
        if id_token_hint:
            params["id_token_hint"] = id_token_hint
        redirect_uri = post_logout_redirect_uri or self.redirect_uri
        if redirect_uri:
            params["post_logout_redirect_uri"] = redirect_uri

        query_str = f"?{urlencode(params)}" if params else ""
        return f"{self.base_url}{LOGOUT_PATH}{query_str}"
