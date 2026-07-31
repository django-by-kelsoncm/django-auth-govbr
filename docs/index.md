# Visão Geral - django-auth-govbr

O **`django-auth-govbr`** (`django_govbr_auth`) é uma solução completa, extensível e pronta para produção que integra o **Login Único do Governo Federal (Gov.br)** a aplicações Django.

A biblioteca implementa o padrão **OpenID Connect (OIDC)** com **PKCE (Proof Key for Code Exchange)** conforme as normas de segurança exigidas pelo Governo Federal do Brasil.

---

## Principais Recursos

- **Conformidade OIDC + PKCE (`S256`)**: Autenticação segura com proteção contra ataques de intercepção de código de autorização.
- **Alternância Simples de Ambiente**: Suporte nativo aos ambientes de Homologação (`staging`) e Produção (`production`).
- **Single Sign-Out (Logout Federated)**: Encerramento de sessão alinhado com o Gov.br utilizando `id_token_hint` e redirecionamento pós-logout.
- **Backend Extensível**: Permite customizar criação e atualização de usuários (`GovBrAuthBackend`).
- **Mapeamento Flexível de Atributos**: Converta automaticamente campos do Gov.br (`sub`, `name`, `email`) para o modelo `User` do Django.
- **100% de Cobertura de Testes Unitários e de Integração**.
