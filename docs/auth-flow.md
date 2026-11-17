# Fluxo de Autenticação e PKCE

O pacote **`django-auth-govbr`** implementa o fluxo de **Authorization Code com PKCE (Proof Key for Code Exchange - RFC 7636)**.

## O que é PKCE e por que é utilizado?

O PKCE adiciona uma camada de segurança essencial contra ataques de intercepção de código de autorização em redes públicas ou navegadores.

### Como funciona:

1. **Geração do Par PKCE**:
   - `code_verifier`: String criptograficamente aleatória gerada pela aplicação (mínimo 43 caracteres).
   - `code_challenge`: Hash SHA-256 do `code_verifier`, codificado em Base64URL sem preenchimento `=`.
2. **Redirecionamento ao Gov.br**:
   - A aplicação envia o `code_challenge` e `code_challenge_method=S256` na URL de autorização.
   - O `code_verifier`, o `state` e o `nonce` são salvos na sessão do Django (o `nonce` também vai na URL).
   - Um parâmetro `next` local e seguro é guardado na sessão e usado no fim do callback.
3. **Troca do Código pelo Token**:
   - Após o usuário se autenticar no Gov.br, o callback retorna o `code`.
   - A aplicação recupera o `code_verifier` da sessão e o envia ao endpoint `/token`.
   - O servidor do Gov.br valida se `SHA256(code_verifier) == code_challenge` antes de emitir os tokens.

```
+--------+                               +---------------+
|        |--(A)- Redireciona com -------->|               |
|        |       code_challenge & state  |               |
|        |                               |               |
|        |<--(B)- Callback com code <-----|  Gov.br SSO   |
| Django |        & state                |               |
|  App   |                               |               |
|        |--(C)- POST /token com -------->|               |
|        |       code & code_verifier    |               |
|        |                               |               |
|        |<--(D)- Retorna access_token <--|               |
+--------+        & id_token             +---------------+
```

## `state` e `nonce`

- O `state` devolvido pelo Gov.br é comparado em tempo constante (`secrets.compare_digest`) com o da sessão; diferença
  ou ausência levanta `GovBrStateMismatchError` (proteção contra CSRF).
- Com `USE_NONCE` (padrão), o claim `nonce` do `id_token` é comparado com o da sessão; diferença, ausência ou `id_token`
  ilegível levanta `GovBrNonceMismatchError` (proteção contra replay).
- A assinatura do `id_token` **não** é verificada: ele chega direto do endpoint `/token` por TLS, caso em que o OIDC Core
  (3.1.3.7, item 6) aceita a validação do servidor TLS no lugar da assinatura.
- `state`, `code_verifier`, `nonce` e `next` são removidos da sessão no callback, com sucesso ou falha.

## Autenticação no `/token`

Por padrão (`TOKEN_AUTH_METHOD = "client_secret_basic"`) o cliente envia `CLIENT_ID:CLIENT_SECRET` em HTTP Basic, como
documenta o roteiro técnico do Login Único. Use `"client_secret_post"` para enviar as credenciais no corpo.

Depois do perfil, a sessão local é aberta pelo [login handler](login-handlers.md).
