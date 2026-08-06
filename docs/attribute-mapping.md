# Mapeamento de Atributos do Gov.br para o Django User Model

O pacote traduz automaticamente o perfil do usuário retornado pelo endpoint `/userinfo` do Gov.br em campos do modelo `User` do Django (seja o modelo padrão ou customizado via `AUTH_USER_MODEL`).

## Mapeamento Padrão

```python
DEFAULT_USER_ATTR_MAP = {
    "username": "sub",
    "email": "email",
    ("first_name", "last_name"): "name",
}
```

---

## Formatos de Mapeamento Suportados

### 1. Campo Simples ou Aninhado (Dotted Path)
- `"campo_django": "campo_govbr"` associa diretamente o valor da chave retornado pelo Gov.br ao modelo do Django.
- `"campo_django": "dados.cpf"` permite acessar chaves em dicionários aninhados utilizando notação de ponto.
- `"raw_data": "fulljson"` associa o dicionário bruto retornado pelo Gov.br ao campo especificado.

### 2. Divisão de Nome Completo (Tupla)
`("first_name", "last_name"): "name"` pega a string enviada na chave `name` do Gov.br (ex: `"Ana Maria Silva"`) e atribui o primeiro nome (`"Ana"`) para `first_name` e o restante (`"Maria Silva"`) para `last_name`.

### 3. Lambdas e Callables Customizadas
```python
"USER_ATTR_MAP": {
    "username": "sub",
    "full_name": lambda info: f"Gov. {info.get('name')}",
}
```

### 4. Dicionários de Especificação (`dict` spec) e Transformadores
```python
"USER_ATTR_MAP": {
    "username": "sub",
    "cpf": {
        "key": "sub",
        "transform": "django_govbr_auth.transformers.format_cpf",
    },
    "picture_url": {
        "key": "picture",
    },
}
```

---

## Mapeamento de Fotos (URL vs Download para ImageField)

### Caso A: Mapear apenas a URL da foto
```python
"USER_ATTR_MAP": {
    "foto_url": "picture",
}
```

### Caso B: Baixar a foto e salvar em ImageField / FileField
```python
"USER_ATTR_MAP": {
    "foto": {
        "key": "picture",
        "transform": "django_govbr_auth.transformers.fetch_image_file",
    },
}
```

---

## Transformadores Embutidos (`django_govbr_auth.transformers`)

- `fetch_image_file`: baixa a imagem da URL informada e retorna um `ContentFile` do Django.
- `parse_date`: converte string ISO (`YYYY-MM-DD`) para `datetime.date`.
- `format_cpf`: formata CPF (`XXX.XXX.XXX-XX`).
- `to_upper` / `to_lower` / `to_bool`.

---

## Class-Based Mapper Customizado (`USER_MAPPER`)

```python
# mappers.py
from django_govbr_auth.mappers import BaseGovBrUserMapper

class CustomGovBrUserMapper(BaseGovBrUserMapper):
    def map_attributes(self, user_info, attr_map=None):
        attrs = super().map_attributes(user_info, attr_map)
        attrs["custom_flag"] = True
        return attrs
```

```python
# settings.py
GOVBR_AUTH = {
    ...
    "USER_MAPPER": "meu_app.mappers.CustomGovBrUserMapper",
}
```
