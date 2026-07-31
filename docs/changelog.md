# Histórico de Mudanças (Changelog)

Todas as mudanças relevantes no projeto `django-auth-govbr` serão documentadas neste arquivo.

## [1.0.0] - 2026-07-31

### Adicionado
- Implementação inicial da biblioteca `django-auth-govbr`.
- Suporte nativo ao protocolo **OpenID Connect (OIDC)** com **PKCE (SHA-256 / `S256`)**.
- Suporte a ambientes de Homologação (`staging`) e Produção (`production`).
- Backend de autenticação extensível `GovBrAuthBackend`.
- Mapeamento flexível de atributos (`DEFAULT_USER_ATTR_MAP`).
- Support para Single Sign-Out (Logout federado) com `GovBrLogoutView`.
- Cobertura de testes unitários de 100% via `pytest` e `pytest-cov`.
- Aplicação Sandbox de demonstração (`sandbox/`).
