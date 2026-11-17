# Login Handlers (Sessão Local)

Depois que o callback confere `state` e `nonce`, troca o código pelo token e busca o perfil, ele entrega o resultado ao
**login handler** configurado em `GOVBR_AUTH["LOGIN_HANDLER"]`. O handler decide como abrir a sessão local, como
tratar erros e como encerrar a sessão no logout.

## Handler padrão: `DjangoAuthLoginHandler`

Mantém o comportamento das versões anteriores:

1. `authenticate(request, govbr_user_info=user_info)` nos `AUTHENTICATION_BACKENDS` (normalmente o `GovBrAuthBackend`);
2. `login(request, user, backend=GOVBR_AUTH["BACKEND"])`;
3. redireciona para o `next` (se for um caminho local seguro) ou para `LOGIN_REDIRECT_URL`.

No logout chama `django.contrib.auth.logout`. Não é preciso configurar nada para usá-lo.

## Projetos sem `django.contrib.auth`

Se as contas não ficam no banco do Django (por exemplo, um provedor de login que delega as contas a uma API), escreva um
handler herdando de `BaseLoginHandler`. Ele **não** importa `django.contrib.auth`; basta haver sessão
(`SessionMiddleware`).

```python
# meu_app/govbr.py
from django.http import HttpResponseRedirect
from django.shortcuts import render

from django_govbr_auth.exceptions import GovBrUserNotAllowedError
from django_govbr_auth.handlers import BaseLoginHandler

from meu_app import api


class ApiLoginHandler(BaseLoginHandler):
    def login(self, request, user_info, token_data, next_url=None):
        conta = api.conta_do_cpf(user_info["sub"], nome=user_info.get("name"), email=user_info.get("email"))
        if conta is None:
            raise GovBrUserNotAllowedError("Conta bloqueada")  # vira self.error(...)
        request.session.cycle_key()  # evita fixação de sessão
        request.session["usuario"] = conta["uuid"]
        return HttpResponseRedirect(self.get_success_url(request, next_url))

    def error(self, request, exc):
        return render(request, "meu_app/erro_govbr.html", {"erro": self.get_error_message(exc)}, status=400)

    def logout(self, request):
        request.session.flush()
```

```python
GOVBR_AUTH = {
    # ...
    "LOGIN_HANDLER": "meu_app.govbr.ApiLoginHandler",
}
```

`LOGIN_HANDLER` aceita o caminho de importação, a própria classe ou uma instância.

## Métodos

| Método | Padrão em `BaseLoginHandler` | Quando é chamado |
|---|---|---|
| `login(request, user_info, token_data, next_url=None)` | abstrato (`NotImplementedError`) | callback válido; deve devolver a resposta |
| `error(request, exc)` | `messages.error` + redireciona para `LOGIN_URL` | qualquer falha do callback, inclusive as levantadas por `login` |
| `logout(request)` | `request.session.flush()` | `GovBrLogoutView`, antes do logout federado |
| `get_error_message(exc)` | mensagem traduzível conforme o tipo da exceção | usado por `error` |
| `get_success_url(request, next_url)` | `next` local seguro ou `LOGIN_REDIRECT_URL` | usado por `login` |

O `id_token` é guardado na sessão (`govbr_id_token`) **depois** de `login`, então pode trocar a chave da sessão à vontade.

## Exceções entregues a `error`

| Exceção | Causa |
|---|---|
| `GovBrProviderError` | o Gov.br voltou com `?error=` (ex.: usuário cancelou); tem `error` e `description` |
| `GovBrStateMismatchError` | `state` ausente ou diferente, ou sem `code_verifier` na sessão |
| `GovBrNonceMismatchError` | `nonce` do `id_token` ausente ou diferente (subclasse de `GovBrStateMismatchError`) |
| `GovBrTokenError` | falha ao trocar o código pelo token |
| `GovBrUserInfoError` | falha ao buscar o perfil em um endpoint obrigatório |
| `GovBrUserNotAllowedError` / `GovBrAuthenticationError` | recusa na autenticação local |
| outras | erro inesperado (registrado com `logger.exception`) |
