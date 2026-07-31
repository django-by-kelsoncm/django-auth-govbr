import base64
import hashlib
import secrets

from django.core.exceptions import ImproperlyConfigured

STAGING_BASE_URL = "https://sso.staging.acesso.gov.br"
PRODUCTION_BASE_URL = "https://sso.acesso.gov.br"

# Default mapping: user model field → Gov.br response key.
# A tuple key means "split the Gov.br value on the first space and assign
# the first part to key[0] and the remainder to key[1]".
DEFAULT_USER_ATTR_MAP = {
    "username": "sub",
    "email": "email",
    ("first_name", "last_name"): "name",
}


def get_govbr_settings():
    """Read and validate GOVBR_AUTH settings from Django settings.

    Expects a single GOVBR_AUTH dictionary with configuration:

    GOVBR_AUTH = {
        'CLIENT_ID': 'your-id',
        'CLIENT_SECRET': 'your-secret',
        'REDIRECT_URI': 'https://example.com/callback/',
        'ENVIRONMENT': 'staging',  # 'staging' or 'production' (default: 'staging')
        'BASE_URL': None,  # optional override
        'SCOPES': ['openid', 'email', 'profile'],  # optional
        'USER_LOOKUP_FIELD': 'username',  # optional
        'USER_ATTR_MAP': {...},  # optional
        'USER_JSON_FIELD': None,  # optional
        'DIRECT_REDIRECT': True,  # optional
        'POST_LOGOUT_REDIRECT_URI': None,  # optional
    }
    """
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

    return {
        "client_id": govbr_auth["CLIENT_ID"],
        "client_secret": govbr_auth["CLIENT_SECRET"],
        "redirect_uri": govbr_auth["REDIRECT_URI"],
        "environment": environment,
        "base_url": base_url,
        "scopes": govbr_auth.get("SCOPES", ["openid", "email", "profile"]),
        "user_lookup_field": govbr_auth.get("USER_LOOKUP_FIELD", "username"),
        "user_attr_map": govbr_auth.get("USER_ATTR_MAP", DEFAULT_USER_ATTR_MAP),
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
    keys = dotted_key.split(".")
    value = data
    for key in keys:
        if not isinstance(value, dict):
            return None
        value = value.get(key)
        if value is None:
            return None
    return value


def apply_user_attr_map(user_info, attr_map):
    """Translate a Gov.br user_info dict into a flat dict of user model field→value pairs."""
    result = {}
    for model_field, govbr_key in attr_map.items():
        if govbr_key == "fulljson":
            result[model_field] = user_info
            continue
        value = _extract_nested(user_info, govbr_key)
        if value is None:
            continue
        if isinstance(model_field, (list, tuple)) and len(model_field) == 2:
            field_a, field_b = model_field
            parts = str(value).split(" ", 1)
            result[field_a] = parts[0]
            result[field_b] = parts[1] if len(parts) > 1 else ""
        else:
            result[model_field] = value
    return result


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
