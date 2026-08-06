# Configuração

O comportamento do pacote é controlado através do dicionário `GOVBR_AUTH` no arquivo `settings.py` do seu projeto Django.

## Exemplo de Configuração Básica

```python
# settings.py

INSTALLED_APPS = [
    # ...
    "django.contrib.auth",
    "django_govbr_auth",
]

AUTHENTICATION_BACKENDS = [
    "django_govbr_auth.backends.GovBrAuthBackend",
    "django.contrib.auth.backends.ModelBackend",
]

GOVBR_AUTH = {
    "CLIENT_ID": "seu-client-id-govbr",
    "CLIENT_SECRET": "seu-client-secret-govbr",
    "REDIRECT_URI": "https://sua-aplicacao.gov.br/auth/govbr/callback/",
    "ENVIRONMENT": "staging",  # "staging" ou "production"
}

LOGIN_URL = "/auth/govbr/login/"
LOGIN_REDIRECT_URL = "/dashboard/"
LOGOUT_REDIRECT_URL = "/"
```

## Opções de Configuração

### Parâmetros Obrigatórios

- **`CLIENT_ID`** (`str`): ID do cliente fornecido pelo provedor Gov.br.
- **`CLIENT_SECRET`** (`str`): Chave secreta fornecida pelo provedor Gov.br.
- **`REDIRECT_URI`** (`str`): URI de redirecionamento autorizada cadastrada no Login Único.

### Parâmetros Opcionais

- **`ENVIRONMENT`** (`str`, padrão: `"staging"`):
  - `"staging"`: Utiliza `https://sso.staging.acesso.gov.br`
  - `"production"`: Utiliza `https://sso.acesso.gov.br`
- **`BASE_URL`** (`str`, padrão: `None`): URL base do provedor SSO Gov.br. Caso especificada, sobrescreve a URL derivada de `ENVIRONMENT`.
- **`SCOPES`** (`list`, padrão: `["openid", "email", "profile"]`): Lista de escopos OIDC solicitados durante a autorização.
- **`USER_LOOKUP_FIELD`** (`str`, padrão: `"username"`): Campo do modelo `User` utilizado para buscar e identificar unicamente o usuário localmente.
- **`USER_ATTR_MAP`** (`dict`, padrão: `DEFAULT_USER_ATTR_MAP`): Mapeamento de atributos retornado pelo `/userinfo` para o modelo `User`.
- **`USER_INFO_FETCHERS`** (`list`, padrão: `["django_govbr_auth.fetchers.DefaultEndpointsUserInfoFetcher"]`): Lista de classes fetcher executadas na Cadeia de Responsabilidade.
- **`USER_INFO_ENDPOINTS`** (`list`, padrão: `["/userinfo"]`): Lista de endpoints OIDC/API a consultar e mesclar.
- **`USER_INFO_MAPPERS`** (`list`, padrão: `["django_govbr_auth.mappers.DefaultAttrMapUserMapper"]`): Lista de classes mapper executadas na Cadeia de Responsabilidade.
- **`USER_JSON_FIELD`** (`str`, padrão: `None`): Campo `JSONField` para gravar a resposta bruta da API do Gov.br no modelo `User`.
- **`CREATE_USER`** (`bool`, padrão: `True`): Se definido como `False`, lança `GovBrUserNotAllowedError` caso o usuário ainda não possua conta local.
- **`USER_DEFAULTS`** (`dict`, padrão: `{"is_active": True}`): Atributos padrão aplicados na criação e sincronizados a cada login.
- **`FIRST_USER_DEFAULTS`** (`dict`, padrão: `None`): Atributos aplicados exclusivamente ao primeiro usuário criado no sistema (ex: `{"is_superuser": True, "is_staff": True}`).
- **`UPDATE_FIELDS_ON_CREATE`** (`list` ou `None`, padrão: `None`): Lista de campos a serem preenchidos na criação do usuário (`None` representa todos).
- **`UPDATE_FIELDS_ON_LOGIN`** (`list` ou `None`, padrão: `None`): Lista de campos atualizados a cada login do usuário (`None` representa todos).
- **`DIRECT_REDIRECT`** (`bool`, padrão: `True`): Se `True`, o usuário é redirecionado imediatamente ao Gov.br. Se `False`, renderiza a página intermediária `django_govbr_auth/login.html`.
- **`POST_LOGOUT_REDIRECT_URI`** (`str`, padrão: `None`): URI de retorno após realizar o logout federado OIDC.
- **`BACKEND`** (`str`, padrão: `"django_govbr_auth.backends.GovBrAuthBackend"`): Caminho da classe backend de autenticação.
