# django-auth-govbr

[![PyPI version](https://img.shields.io/pypi/v/django-auth-govbr.svg)](https://pypi.org/project/django-auth-govbr/)
[![Python Versions](https://img.shields.io/pypi/pyversions/django-auth-govbr.svg)](https://pypi.org/project/django-auth-govbr/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Backend de autenticação Django extensível e moderno para integração com o **Login Único do Governo Federal (Gov.br)** via **OpenID Connect (OIDC)** com **PKCE (Proof Key for Code Exchange)**.

---

## 🛠️ Recursos

- **OpenID Connect (OIDC) com PKCE (`S256`)**: Atende aos padrões e recomendações de segurança do Login Único Gov.br.
- **Suporte Nativo a Ambientes**: Alterna facilmente entre Homologação (`https://sso.staging.acesso.gov.br`) e Produção (`https://sso.acesso.gov.br`).
- **Single Sign-Out (Logout)**: View e cliente com suporte a logout federado OIDC via `id_token_hint` e `post_logout_redirect_uri`.
- **Mapeamento de Atributos Customizável**: Mapeie facilmente campos da API do Gov.br (`sub`, `name`, `email`, etc.) para o modelo de usuário do Django.
- **Extensibilidade**: Sobrescreva métodos do `GovBrAuthBackend` para controlar criação e atualização de usuários.
- **100% de Cobertura de Testes**.

---

## 📦 Instalação

```bash
pip install django-auth-govbr
```

---

## 🚀 Configuração Rápida

### 1. Adicione às `INSTALLED_APPS` e `AUTHENTICATION_BACKENDS`

No seu `settings.py`:

```python
INSTALLED_APPS = [
    # ...
    "django.contrib.auth",
    "django_govbr_auth",
]

AUTHENTICATION_BACKENDS = [
    "django_govbr_auth.backends.GovBrAuthBackend",
    "django.contrib.auth.backends.ModelBackend",
]
```

### 2. Configure as credenciais em `GOVBR_AUTH`

```python
GOVBR_AUTH = {
    "CLIENT_ID": "seu-client-id-govbr",
    "CLIENT_SECRET": "seu-client-secret-govbr",
    "REDIRECT_URI": "https://sua-aplicacao.gov.br/auth/govbr/callback/",
    "ENVIRONMENT": "staging",  # "staging" ou "production"
}
```

### 3. Inclua as URLs do pacote

No seu `urls.py` principal:

```python
from django.urls import include, path

urlpatterns = [
    # ...
    path("auth/govbr/", include("django_govbr_auth.urls")),
]
```

---

## ⚙️ Opções de Configuração (`GOVBR_AUTH`)

| Chave | Tipo | Padrão | Descrição |
| :--- | :--- | :--- | :--- |
| `CLIENT_ID` | `str` | **Obrigatório** | ID do cliente fornecido pelo Gov.br |
| `CLIENT_SECRET` | `str` | **Obrigatório** | Segredo do cliente fornecido pelo Gov.br |
| `REDIRECT_URI` | `str` | **Obrigatório** | URI de callback cadastrado no Gov.br |
| `ENVIRONMENT` | `str` | `"staging"` | `"staging"` ou `"production"` |
| `BASE_URL` | `str` | `None` | URL customizada para o servidor SSO (opcional) |
| `SCOPES` | `list` | `["openid", "email", "profile"]` | Escopos OIDC solicitados |
| `USER_LOOKUP_FIELD` | `str` | `"username"` | Campo do modelo User usado para busca local |
| `USER_ATTR_MAP` | `dict` | Mapeia `sub` → `username`, `email` → `email`, `name` → `(first_name, last_name)` | Mapeamento de campos do Gov.br |
| `CREATE_USER` | `bool` | `True` | Se cria usuário local caso não exista |
| `DIRECT_REDIRECT` | `bool` | `True` | Se redireciona direto ao Gov.br ou exibe confirmação |
| `POST_LOGOUT_REDIRECT_URI` | `str` | `None` | URI de retorno após o Single Sign-Out |

---

## 🧪 Testes

Para rodar a suíte de testes com cobertura:

```bash
uv run --extra dev python -m pytest --cov=django_govbr_auth --cov-report=term-missing
```

---

## 📄 Licença

Este projeto está licenciado sob a licença MIT - consulte o arquivo [LICENSE](LICENSE) para mais detalhes.
