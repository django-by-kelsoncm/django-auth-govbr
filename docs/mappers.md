# Mappers (Mapeamento de Atributos do Gov.br)

O `django-auth-govbr` utiliza o padrão **Chain of Responsibility (Cadeia de Responsabilidade)** para converter o dicionário de atributos do cidadão retornado pelo Gov.br (`user_info`) em campos do modelo `User` do Django.

---

## Como Funcionam os Mappers

A cadeia de mappers (`USER_INFO_MAPPERS`) é executada imediatamente após a consulta dos fetchers. Cada mapper recebe o dicionário `user_info` unificado e o dicionário de campos `attrs` a ser aplicado no modelo `User`.

```
[user_info consolidado] ──> Mapper 1 (DefaultAttrMapUserMapper)
                                │ attrs = {'username': '12345678900', 'email': '...'}
                                ▼
                            Mapper 2 (Mapper Customizado / Permissões)
                                │ attrs final
                                ▼
                            GovBrAuthBackend (get_or_create)
```

---

## Configuração: `USER_INFO_MAPPERS`

No `settings.py`, configure a lista de mappers em `GOVBR_AUTH`:

```python
GOVBR_AUTH = {
    # ...
    "USER_INFO_MAPPERS": [
        "django_govbr_auth.mappers.DefaultAttrMapUserMapper",
        "meu_app.mappers.CustomGovBrMapper",
    ],
}
```

---

## Mapper Padrão: `DefaultAttrMapUserMapper`

O mapper padrão aplica as regras definidas no dicionário `USER_ATTR_MAP` em `GOVBR_AUTH`.

### Formatos de Regras em `USER_ATTR_MAP`

#### 1. Mapeamento Direto ou Dotted Path
```python
"USER_ATTR_MAP": {
    "username": "sub",       # CPF do cidadão no Gov.br
    "email": "email",
    "orgao": "vinculo.orgao",# acessa dicionário aninhado
}
```

#### 2. Dicionário Bruto Completo (`fulljson`)
```python
"USER_ATTR_MAP": {
    "govbr_data": "fulljson", # atribui o dict user_info completo ao campo
}
```

#### 3. Divisão de Nome Completo (Tupla)
```python
"USER_ATTR_MAP": {
    ("first_name", "last_name"): "name",
    # "Ana Maria Silva" -> first_name="Ana", last_name="Maria Silva"
}
```

#### 4. Lambdas e Callables Customizados
```python
"USER_ATTR_MAP": {
    "is_staff": lambda info: info.get("sub") in LISTA_ADMINISTRADORES,
}
```

#### 5. Especificação com Transformadores (`dict` spec)
```python
"USER_ATTR_MAP": {
    "cpf_formatado": {
        "key": "sub",
        "transform": "django_govbr_auth.transformers.format_cpf",
    },
    "foto": {
        "key": "picture",
        "transform": "django_govbr_auth.transformers.fetch_image_file",
    },
}
```

---

## Transformadores Embutidos (`django_govbr_auth.transformers`)

- `fetch_image_file`: baixa a imagem e retorna um `ContentFile` do Django.
- `parse_date`: converte string de data ISO em `datetime.date`.
- `format_cpf`: formata CPF (`XXX.XXX.XXX-XX`).
- `to_upper` / `to_lower` / `to_bool`.

---

## Criando um Mapper Customizado

Para criar um mapper customizado, herde de `BaseUserMapper` (ou do seu alias `BaseGovBrUserMapper`):

```python
# meu_app/mappers.py
from django_govbr_auth.mappers import BaseUserMapper

class CustomGovBrMapper(BaseUserMapper):
    """Mapper que atribui permissões corporativas com base nos atributos do Gov.br."""

    def map_attributes(self, user_info, attrs=None):
        attrs = super().map_attributes(user_info, attrs)
        
        # Exemplo: define is_staff caso o cidadão possua selo de confiabilidade Prata ou Ouro
        if user_info.get("nivel_confiabilidade") in ("prata", "ouro"):
            attrs["is_staff"] = True
            
        return attrs
```

---

## Funções Utilitárias da API de Mappers

- `get_user_info_mappers(cfg=None)`: retorna a lista de instâncias dos mappers configurados.
- `run_user_info_mapper_chain(user_info, attr_map=None, cfg=None)`: executa a cadeia de mappers e retorna o dicionário `attrs` final.
