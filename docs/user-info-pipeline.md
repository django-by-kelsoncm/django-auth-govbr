# Pipeline de Busca e Mapeamento de Perfil

O `django-govbr-auth` utiliza o padrão de projeto **Chain of Responsibility (Cadeia de Responsabilidade)** para busca de dados (`USER_INFO_FETCHERS`) e mapeamento de atributos (`USER_INFO_MAPPERS`).

---

## 1. Cadeia de Busca (`USER_INFO_FETCHERS`)

O elo padrão `DefaultEndpointsUserInfoFetcher` consome os endpoints em `USER_INFO_ENDPOINTS`:

```python
GOVBR_AUTH = {
    "USER_INFO_ENDPOINTS": [
        "/userinfo",
    ],
}
```

Você pode estender a cadeia `USER_INFO_FETCHERS` no `settings.py` para consultar APIs externas ou LDAP:

```python
# meu_app/fetchers.py
from django_govbr_auth.fetchers import BaseUserInfoFetcher

class ExternalLdapFetcher(BaseUserInfoFetcher):
    def fetch(self, client, access_token, user_info=None):
        user_info = super().fetch(client, access_token, user_info)
        cpf = user_info.get("sub")
        if cpf:
            user_info["ldap"] = meu_ldap.buscar_por_cpf(cpf)
        return user_info
```

```python
# settings.py
GOVBR_AUTH = {
    "USER_INFO_FETCHERS": [
        "django_govbr_auth.fetchers.DefaultEndpointsUserInfoFetcher",
        "meu_app.fetchers.ExternalLdapFetcher",
    ],
}
```

---

## 2. Cadeia de Mapeamento (`USER_INFO_MAPPERS`)

O elo padrão `DefaultAttrMapUserMapper` aplica o dicionário de regras `USER_ATTR_MAP`:

```python
GOVBR_AUTH = {
    "USER_INFO_MAPPERS": [
        "django_govbr_auth.mappers.DefaultAttrMapUserMapper",
    ],
    "USER_ATTR_MAP": {
        "username": "sub",
        "email": "email",
        "cpf": {
            "key": "sub",
            "transform": "django_govbr_auth.transformers.format_cpf",
        },
        "foto": {
            "key": "picture",
            "transform": "django_govbr_auth.transformers.fetch_image_file",
        },
    },
}
```
