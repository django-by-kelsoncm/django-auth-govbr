# Histórico de Mudanças (Changelog)

Todas as mudanças relevantes no projeto `django-auth-govbr` serão documentadas neste arquivo.

## [1.3.0] - 2026-11-17

### Adicionado
- `GOVBR_AUTH["LOGIN_HANDLER"]` e `django_govbr_auth.handlers` (`BaseLoginHandler`, `DjangoAuthLoginHandler`): o callback delega a sessão local, o tratamento de erros e o logout a um handler configurável. Permite usar a biblioteca em projetos sem `django.contrib.auth` nem banco.
- `nonce` OIDC no `/authorize`, conferido no `id_token` (`USE_NONCE`, padrão `True`), e `GovBrNonceMismatchError`.
- `TOKEN_AUTH_METHOD` (`client_secret_basic` ou `client_secret_post`).
- `GovBrProviderError` para o retorno do Gov.br com `?error=`.
- Chave `required` em `USER_INFO_ENDPOINTS`.
- Mensagens de erro traduzíveis (`gettext_lazy`).

### Alterado
- **O `/token` passa a usar HTTP Basic por padrão** (`client_secret_basic`), como documenta o roteiro técnico do Login Único. Para o comportamento anterior, use `"TOKEN_AUTH_METHOD": "client_secret_post"`.
- **Falha no `/userinfo` agora interrompe o login** (`GovBrUserInfoError`); antes era só registrada em log e o login seguia sem perfil.
- O `next` é guardado na sessão no início do login (o Gov.br não o devolve no callback); o `next` na query do callback continua aceito.
- O `state` é comparado em tempo constante; `state`, `code_verifier` e `nonce` são consumidos mesmo quando o callback falha.
- `django.contrib.auth` só é importado pelo handler padrão.

### Corrigido
- Testes quebrados na `main` (issue #8): `resolve_callable` volta a existir como alias, `apply_user_attr_map` volta a respeitar o `attr_map` recebido e a cobertura volta a 100%.

## [1.0.0] - 2026-07-31

### Adicionado
- Implementação inicial da biblioteca `django-auth-govbr`.
- Suporte nativo ao protocolo **OpenID Connect (OIDC)** com **PKCE (SHA-256 / `S256`)**.
- Suporte a ambientes de Homologação (`staging`) e Produção (`production`).
- Backend de autenticação extensível `GovBrAuthBackend`.
- Mapeamento flexível de atributos (`DEFAULT_USER_ATTR_MAP`).
- Support para Single Sign-Out (Logout federado) com `GovBrLogoutView`.
- Cobertura de testes unitários de 100% via `pytest` e `pytest-cov`.
- Aplicação Sandbox de demonstração (`sandbox/`).
