# Referência da API

## `django_govbr_auth.backends.GovBrAuthBackend`

Backend de autenticação responsável por integrar a resposta do Gov.br com o modelo de usuário do Django.

### Métodos Principais

#### `authenticate(request, govbr_user_info=None, **kwargs)`
Método principal chamado pelo Django. Processa as informações do usuário e retorna a instância de `User`.

#### `get_user_attrs(govbr_user_info, cfg)`
Converte o perfil bruto em um dicionário de atributos do modelo `User`.

#### `get_lookup_value(attrs, lookup_field)`
Extrai o valor de busca (ex: valor do `username`/`sub`) do dicionário mapeado.

#### `get_or_create_user(lookup_field, lookup_value, mapped_attrs, cfg)`
Busca o usuário no banco local ou chama `create_user` caso ele não exista. Lança `GovBrUserNotAllowedError` se `CREATE_USER` for `False`.

#### `create_user(lookup_field, lookup_value, mapped_attrs, cfg)`
Instancia e salva um novo usuário no banco de dados.

#### `update_user(user, mapped_attrs, cfg)`
Sincroniza os atributos alterados no login de um usuário existente.

---

## `django_govbr_auth.client.GovBrOAuth2Client`

Cliente de baixo nível para interação HTTP com as APIs do Gov.br.
Construtor: `GovBrOAuth2Client(client_id, client_secret, redirect_uri, scopes=None, base_url=None, token_auth_method="client_secret_basic")`.

### Métodos

- `get_authorization_url(state, code_challenge, nonce=None)`: Retorna a URL completa de autorização com parâmetros PKCE (`S256`) e, se informado, o `nonce`.
- `exchange_code_for_token(code, code_verifier, timeout=30)`: Troca o código pelo `access_token` e `id_token`, autenticando-se por HTTP Basic ou no corpo conforme `token_auth_method`.
- `get_user_info(access_token, timeout=30)`: Consulta o perfil do usuário no endpoint `/userinfo`.
- `get_logout_url(id_token_hint=None, post_logout_redirect_uri=None)`: Retorna a URL de logout OIDC.

---

## `django_govbr_auth.handlers`

- `BaseLoginHandler`: Base dos login handlers (`login`, `error`, `logout`, `get_error_message`, `get_success_url`). Veja [Login Handlers](login-handlers.md).
- `DjangoAuthLoginHandler`: Handler padrão, com `authenticate`/`login`/`logout` do `django.contrib.auth`.
- `get_login_handler(cfg)`: Instancia o handler de `GOVBR_AUTH["LOGIN_HANDLER"]`.
- `safe_next_url(request, next_url)`: Reduz `next_url` a um caminho local seguro, ou `None`.

## `django_govbr_auth.utils`

- `generate_state()`, `generate_nonce()`, `generate_pkce_pair()`: Valores aleatórios do fluxo.
- `decode_jwt_payload(token)`: Lê os claims de um JWT **sem verificar a assinatura** (só para o `id_token` recebido do `/token` por TLS).

---

## `django_govbr_auth.exceptions`

- `GovBrAuthError`: Exceção base do pacote.
- `GovBrStateMismatchError`: Erro de divergência de estado (CSRF).
- `GovBrNonceMismatchError`: `nonce` do `id_token` ausente ou divergente (subclasse de `GovBrStateMismatchError`).
- `GovBrProviderError`: O Gov.br voltou ao callback com `?error=` (atributos `error` e `description`).
- `GovBrTokenError`: Falha na troca do código de autorização pelo token.
- `GovBrUserInfoError`: Falha ao consultar os dados do perfil do usuário.
- `GovBrUserNotAllowedError`: Lançado quando a criação de novos usuários está desativada (`CREATE_USER=False`).
- `GovBrAuthenticationError`: Erro geral durante o fluxo de autenticação.
