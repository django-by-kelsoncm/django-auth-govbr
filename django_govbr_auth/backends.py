from django.contrib.auth import get_user_model

from .exceptions import GovBrUserNotAllowedError
from .utils import apply_user_attr_map, get_govbr_settings


def _filter_fields(attrs, allowed):
    """Return a subset of *attrs* restricted to *allowed* field names.

    ``allowed=None`` means no restriction (return all fields).
    ``allowed=[]`` means return an empty dict.
    """
    if allowed is None:
        return dict(attrs)
    return {k: v for k, v in attrs.items() if k in allowed}


class GovBrAuthBackend:
    """
    Django authentication backend for Gov.br OAuth2/OIDC.

    Looks up or creates a Django user based on the profile info returned by Gov.br.

    Behaviour is controlled by ``GOVBR_AUTH`` settings:

    * ``CREATE_USER`` (bool, default ``True``) — when ``False``, raises
      :exc:`~django_govbr_auth.exceptions.GovBrUserNotAllowedError` for users
      that do not yet have a local account.
    * ``USER_DEFAULTS`` (dict, default ``{"is_active": True}``) — extra
      field values applied only when creating a new user.
    * ``UPDATE_FIELDS_ON_CREATE`` (list or ``None``, default ``None``) —
      mapped fields written when a new user is created. ``None`` means all
      mapped fields; ``[]`` means none.
    * ``UPDATE_FIELDS_ON_LOGIN`` (list or ``None``, default ``None``) —
      mapped fields synced on every subsequent login. ``None`` means all
      mapped fields; ``[]`` means none.
    * ``FIRST_USER_DEFAULTS`` (dict or ``None``, default ``None``) — when set,
      these field values are used instead of ``USER_DEFAULTS`` if no users
      exist yet (e.g. ``{"is_superuser": True, "is_staff": True}``).
    """

    def authenticate(self, request, govbr_user_info=None, **kwargs):
        if govbr_user_info is None:
            return None

        cfg = get_govbr_settings()
        lookup_field = cfg["user_lookup_field"]

        attrs = self.get_user_attrs(govbr_user_info, cfg)
        lookup_value = self.get_lookup_value(attrs, lookup_field)
        if not lookup_value:
            return None

        mapped_attrs = {k: v for k, v in attrs.items() if k != lookup_field}
        return self.get_or_create_user(lookup_field, lookup_value, mapped_attrs, cfg)

    # ------------------------------------------------------------------
    # Extension points
    # ------------------------------------------------------------------

    def get_user_attrs(self, govbr_user_info, cfg):
        """Return a dict of model-field → value built from *govbr_user_info*."""
        attrs = apply_user_attr_map(govbr_user_info, cfg["user_attr_map"], cfg=cfg)
        if cfg["json_field"]:
            attrs[cfg["json_field"]] = govbr_user_info
        return attrs

    def get_lookup_value(self, attrs, lookup_field):
        """Return the value used to look up the local user record."""
        return attrs.get(lookup_field)

    def get_or_create_user(self, lookup_field, lookup_value, mapped_attrs, cfg):
        """Fetch the existing user or create a new one."""
        User = get_user_model()
        try:
            user = User.objects.get(**{lookup_field: lookup_value})
        except User.DoesNotExist:
            if not cfg["create_user"]:
                raise GovBrUserNotAllowedError(
                    f"No local account for Gov.br user '{lookup_value}' and CREATE_USER is disabled."
                )
            return self.create_user(lookup_field, lookup_value, mapped_attrs, cfg)

        return self.update_user(user, mapped_attrs, cfg)

    def create_user(self, lookup_field, lookup_value, mapped_attrs, cfg):
        """Instantiate, populate, and save a brand-new local user."""
        User = get_user_model()
        first_defaults = cfg["first_user_defaults"]
        if first_defaults is not None and not User.objects.exists():
            defaults = dict(first_defaults)
        else:
            defaults = dict(cfg["user_defaults"])
        defaults.update(_filter_fields(mapped_attrs, cfg["update_fields_on_create"]))
        user = User(**{lookup_field: lookup_value}, **defaults)
        user.save()
        return user

    def update_user(self, user, mapped_attrs, cfg):
        """Sync *mapped_attrs* onto an existing *user* and save if changed."""
        changed = False

        for field, value in _filter_fields(mapped_attrs, cfg["update_fields_on_login"]).items():
            if getattr(user, field, None) != value:
                setattr(user, field, value)
                changed = True

        for field, value in cfg["user_defaults"].items():
            if getattr(user, field, None) != value:
                setattr(user, field, value)
                changed = True

        if changed:
            user.save()

        return user

    def get_user(self, user_id):
        User = get_user_model()
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
