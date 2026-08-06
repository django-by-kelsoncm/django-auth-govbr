# Fetchers (Busca de Dados do Gov.br)

O `django-auth-govbr` utiliza o padrão **Chain of Responsibility (Cadeia de Responsabilidade)** para consultar o endpoint OIDC `/userinfo` do Gov.br e endpoints adicionais de APIs governamentais ou sistemas internos.

---

## Como Funcionam os Fetchers

Após a conclusão da troca do código OAuth2/OIDC e validação do token PKCE, o `access_token` é obtido e a cadeia de fetchers (`USER_INFO_FETCHERS`) é executada. Cada fetcher recebe o dicionário acumulado `user_info` e realiza chamadas HTTP ou consultas para enriquecê-lo.

```
[Access Token] ──> Fetcher 1 (DefaultEndpointsUserInfoFetcher)
                       │ user_info obtido do /userinfo
                       ▼
                   Fetcher 2 (Fetcher Customizado / LDAP)
                       │ user_info final
                       ▼
                   Cadeia de Mappers
```

---

## Configuração: `USER_INFO_FETCHERS`

No `settings.py`, configure a lista de fetchers em `GOVBR_AUTH`:

```python
GOVBR_AUTH = {
    "CLIENT_ID": "seu-client-id",
    "CLIENT_SECRET": "seu-client-secret",
    "REDIRECT_URI": "https://sua-app.gov.br/auth/govbr/callback/",
    "USER_INFO_FETCHERS": [
        "django_govbr_auth.fetchers.DefaultEndpointsUserInfoFetcher",
        "meu_app.fetchers.ExternalLdapFetcher",
    ],
}
```

---

## Fetcher Padrão: `DefaultEndpointsUserInfoFetcher`

O fetcher padrão consome a lista `USER_INFO_ENDPOINTS` definida em `GOVBR_AUTH` (por padrão `["/userinfo"]`) e efetua chamadas autorizadas para cada endpoint.

### Formatos de Endpoints Suportados (`USER_INFO_ENDPOINTS`)

#### 1. Endpoint Simples (String)
```python
"USER_INFO_ENDPOINTS": [
    "/userinfo",
]
```

#### 2. Endpoint com Formatação Dinâmica (String com `{chave}`)
```python
"USER_INFO_ENDPOINTS": [
    "/userinfo",
    "/api/v1/cidadao/{sub}/dados-complementares/",
]
```
Chaves `{sub}`, `{email}`, etc. são preenchidas dinamicamente a partir dos campos presentes em `user_info`.

#### 3. Especificação por Dicionário (`dict` spec)
Permite isolar respostas sob um *namespace*, extrair listas de respostas paginadas ou iterar sobre coleções:

```python
"USER_INFO_ENDPOINTS": [
    "/userinfo",
    {
        "endpoint": "/api/v1/vinculos/",
        "namespace": "vinculos_gov",
        "extract_list": "results",
    },
    {
        "endpoint": "/api/v1/vinculos/{id}/detalhes/",
        "namespace": "detalhes_vinculos",
        "for_each": "vinculos_gov", # Itera sobre cada item retornado
    },
]
```

---

## Criando um Fetcher Customizado

Para criar um fetcher customizado, herde de `BaseUserInfoFetcher` e sobrescreva o método `fetch`:

```python
# meu_app/fetchers.py
from django_govbr_auth.fetchers import BaseUserInfoFetcher

class ExternalLdapFetcher(BaseUserInfoFetcher):
    """Fetcher que enriquece os dados do cidadão consultando o LDAP corporativo via CPF (sub)."""

    def fetch(self, client, access_token, user_info=None):
        user_info = super().fetch(client, access_token, user_info)
        
        cpf = user_info.get("sub")
        if cpf:
            user_info["ldap_info"] = meu_ldap.buscar_por_cpf(cpf)
            
        return user_info
```

---

## Funções Utilitárias da API de Fetchers

- `get_user_info_fetchers(cfg=None)`: retorna a lista de instâncias dos fetchers configurados.
- `run_user_info_fetcher_chain(client, access_token, cfg=None)`: executa toda a cadeia de fetchers e retorna o dicionário `user_info` consolidado.
