# Single Sign-Out (Logout Federado)

O **`django-auth-govbr`** fornece suporte nativo ao enquadramento de logout OIDC do Gov.br.

## Como Funciona

1. Durante o callback de autenticação bem-sucedido, o pacote salva o `id_token` retornado pelo Gov.br na sessão do Django (`request.session["govbr_id_token"]`).
2. Quando o usuário acessa a view `GovBrLogoutView` (`/auth/govbr/logout/`):
   - A sessão local do Django é encerrada via `logout(request)`.
   - A aplicação redireciona o usuário para o endpoint `/logout` do Gov.br com os parâmetros:
     - `id_token_hint`: O token de identificação salvo na sessão.
     - `post_logout_redirect_uri`: A URL de retorno cadastrada ou especificada.

## Exemplo de Link nos Templates

```html
<a href="{% url 'django_govbr_auth:logout' %}">Sair (Logout Gov.br)</a>
```

## Configuração da URI de Retorno

Você pode definir para onde o usuário deve ser enviado após deslogar no Gov.br:

```python
GOVBR_AUTH = {
    # ...
    "POST_LOGOUT_REDIRECT_URI": "https://sua-aplicacao.gov.br/",
}
```

Caso não seja definida, o pacote utilizará a configuração `LOGOUT_REDIRECT_URL` ou a `REDIRECT_URI`.
