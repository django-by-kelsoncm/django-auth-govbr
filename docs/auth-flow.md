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
   - O `code_verifier` e o `state` são salvos na sessão do Django.
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
