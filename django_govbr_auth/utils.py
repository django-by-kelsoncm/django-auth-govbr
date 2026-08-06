import base64
import hashlib
import secrets

from django.core.exceptions import ImproperlyConfigured

STAGING_BASE_URL = "https://sso.staging.acesso.gov.br"
PRODUCTION_BASE_URL = "https://sso.acesso.gov.br"

DEFAULT_USER_ATTR_MAP = {
    "username": "sub",
    "email": "email",
    ("first_name", "last_name"): "name",
}

DEFAULT_GOVBR_ENDPOINTS = [
    "/userinfo",
]


def get_govbr_settings():
    """Read and validate GOVBR_AUTH settings from Django settings."""
    from django.conf import settings

    govbr_auth = getattr(settings, "GOVBR_AUTH", {})

    # Validate required fields
    required = ["CLIENT_ID", "CLIENT_SECRET", "REDIRECT_URI"]
    missing = [field for field in required if not govbr_auth.get(field)]

    if missing:
        raise ImproperlyConfigured(
            f"Missing required GOVBR_AUTH settings: {', '.join(missing)}. "
            f"Configure GOVBR_AUTH dictionary in settings.py"
        )

    environment = govbr_auth.get("ENVIRONMENT", "staging").lower()
    default_base_url = STAGING_BASE_URL if environment == "staging" else PRODUCTION_BASE_URL
    base_url = govbr_auth.get("BASE_URL") or default_base_url

    # Legacy USER_MAPPER compatibility
    default_mappers = ["django_govbr_auth.mappers.DefaultAttrMapUserMapper"]
    if "USER_MAPPER" in govbr_auth:
        default_mappers = [govbr_auth["USER_MAPPER"]]

    return {
        "client_id": govbr_auth["CLIENT_ID"],
        "client_secret": govbr_auth["CLIENT_SECRET"],
        "redirect_uri": govbr_auth["REDIRECT_URI"],
        "environment": environment,
        "base_url": base_url,
        "scopes": govbr_auth.get("SCOPES", ["openid", "email", "profile"]),
        "user_lookup_field": govbr_auth.get("USER_LOOKUP_FIELD", "username"),
        "user_attr_map": govbr_auth.get("USER_ATTR_MAP", DEFAULT_USER_ATTR_MAP),
        "user_info_fetchers": govbr_auth.get(
            "USER_INFO_FETCHERS", ["django_govbr_auth.fetchers.DefaultEndpointsUserInfoFetcher"]
        ),
        "user_info_endpoints": govbr_auth.get("USER_INFO_ENDPOINTS", DEFAULT_GOVBR_ENDPOINTS),
        "user_info_mappers": govbr_auth.get("USER_INFO_MAPPERS", default_mappers),
        "json_field": govbr_auth.get("USER_JSON_FIELD", None),
        "direct_redirect": govbr_auth.get("DIRECT_REDIRECT", True),
        "post_logout_redirect_uri": govbr_auth.get("POST_LOGOUT_REDIRECT_URI", None),
        "backend": govbr_auth.get("BACKEND", "django_govbr_auth.backends.GovBrAuthBackend"),
        "create_user": govbr_auth.get("CREATE_USER", True),
        "user_defaults": govbr_auth.get("USER_DEFAULTS", {"is_active": True}),
        "first_user_defaults": govbr_auth.get("FIRST_USER_DEFAULTS", None),
        "update_fields_on_create": govbr_auth.get("UPDATE_FIELDS_ON_CREATE", None),
        "update_fields_on_login": govbr_auth.get("UPDATE_FIELDS_ON_LOGIN", None),
    }


def _extract_nested(data, dotted_key):
    """Extract a value from a (possibly nested) dict using a dotted key path."""
    from .mappers import _extract_nested as mapper_extract
    return mapper_extract(data, dotted_key)


def get_user_mapper(cfg=None):
    """Instantiate and return the configured Gov.br user mapper chain or first mapper."""
    from .mappers import get_user_info_mappers
    mappers = get_user_info_mappers(cfg)
    return mappers[0] if mappers else None


def apply_user_attr_map(user_info, attr_map, cfg=None):
    """Translate a Gov.br user_info dict into a flat dict of user model field→value pairs.

    Executes the configured USER_INFO_MAPPERS Chain of Responsibility.
    """
    from .mappers import run_user_info_mapper_chain
    return run_user_info_mapper_chain(user_info, attr_map, cfg=cfg)


def get_oauth2_client():
    """Return a GovBrOAuth2Client configured from Django settings."""
    from .client import GovBrOAuth2Client

    cfg = get_govbr_settings()
    return GovBrOAuth2Client(
        client_id=cfg["client_id"],
        client_secret=cfg["client_secret"],
        redirect_uri=cfg["redirect_uri"],
        scopes=cfg["scopes"],
        base_url=cfg["base_url"],
    )


def generate_state():
    """Generate a cryptographically secure random state token for OAuth2 CSRF protection."""
    return secrets.token_urlsafe(32)


def generate_pkce_pair():
    """Generate a (code_verifier, code_challenge) pair according to RFC 7636 S256."""
    code_verifier = secrets.token_urlsafe(64)
    hashed = hashlib.sha256(code_verifier.encode("ascii")).digest()
    code_challenge = base64.urlsafe_b64encode(hashed).decode("ascii").rstrip("=")
    return code_verifier, code_challenge
