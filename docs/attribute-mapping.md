# Mapeamento de Atributos

O pacote traduz automaticamente o perfil do usuário retornado pelo endpoint `/userinfo` do Gov.br em campos do modelo `User` do Django.

## Mapeamento Padrão

O mapeamento padrão utilizado pelo pacote é:

```python
DEFAULT_USER_ATTR_MAP = {
    "username": "sub",
    "email": "email",
    ("first_name", "last_name"): "name",
}
```

### Regras de Mapeamento

1. **Mapeamento Direto**: `"campo_django": "campo_govbr"` associa diretamente o valor da chave retornado pelo Gov.br ao modelo do Django.
2. **Divisão de Nome Completo**: `("first_name", "last_name"): "name"` pega a string enviada na chave `name` do Gov.br (ex: `"Ana Maria Silva"`) e atribui o primeiro nome (`"Ana"`) para `first_name` e o restante (`"Maria Silva"`) para `last_name`.
3. **Navegação Aninhada**: `"campo_django": "dados.cpf"` permite acessar chaves em dicionários aninhados utilizando notação de ponto.
4. **Objeto Completo**: `"raw_data": "fulljson"` associa o dicionário bruto retornado pelo Gov.br ao campo especificado.

## Exemplo de Customização em `settings.py`

```python
GOVBR_AUTH = {
    "CLIENT_ID": "seu-client-id",
    "CLIENT_SECRET": "seu-client-secret",
    "REDIRECT_URI": "https://exemplo.gov.br/callback/",
    "USER_LOOKUP_FIELD": "username",
    "USER_ATTR_MAP": {
        "username": "sub",
        "email": "email",
        ("first_name", "last_name"): "name",
        "cpf": "sub",
    },
}
```
