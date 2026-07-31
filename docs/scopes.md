# Escopos e Ambientes

## Ambientes Suportados

O **Gov.br** disponibiliza dois ambientes de integração:

### 1. Homologação (`staging`)
- **URL Base**: `https://sso.staging.acesso.gov.br`
- Utilizado durante a fase de desenvolvimento, testes unitários e validação.

### 2. Produção (`production`)
- **URL Base**: `https://sso.acesso.gov.br`
- Utilizado no ambiente de produção.

Para alternar entre ambientes, basta definir a chave `ENVIRONMENT` em `settings.py`:

```python
GOVBR_AUTH = {
    # ...
    "ENVIRONMENT": "production",  # ou "staging"
}
```

---

## Escopos OIDC Padrão e Adicionais

Por padrão, o pacote solicita os escopos OIDC essenciais:

```python
"SCOPES": ["openid", "email", "profile"]
```

### Principais Atributos Retornados pelo Gov.br

- `sub`: CPF do cidadão autenticado (11 dígitos, sem pontuação).
- `name`: Nome completo do cidadão.
- `email`: Endereço de e-mail cadastrado e verificado.
- `email_verified`: Booleano indicando se o e-mail foi verificado.
- `picture`: URL da foto de perfil do usuário (quando disponível).
- `govbr_confiabilidades`: Níveis e selos de confiabilidade da conta (Bronze, Prata, Ouro).
