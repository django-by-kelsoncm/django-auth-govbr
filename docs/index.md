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

---

## Documentação

Explore os tópicos detalhados da documentação:

- 📦 **[Instalação](installation.md)** - Requisitos de ambiente e guia de instalação via `pip`, `uv` ou `poetry`.
- ⚙️ **[Configuração](configuration.md)** - Guia passo a passo para integrar com `settings.py` e `urls.py`.
- 🔐 **[Fluxo & PKCE](auth-flow.md)** - Como funciona o fluxo de autenticação OIDC e geração do desafio PKCE.
- 🗺️ **[Mapeamento de Atributos](attribute-mapping.md)** - Mapeamento de dados do perfil Gov.br para os atributos do `User` Django.
- 🔄 **[Pipeline de Perfil de Usuário](user-info-pipeline.md)** - Como a Cadeia de Responsabilidade consulta e processa o perfil do cidadão.
- 📥 **[Fetchers (Busca de Dados)](fetchers.md)** - Detalhes e exemplos da cadeia de busca de dados do Gov.br e APIs externas.
- 🛠️ **[Mappers (Mapeamento)](mappers.md)** - Detalhes e exemplos da cadeia de mapeamento de atributos para o modelo `User`.
- 🌐 **[Escopos & Ambientes](scopes.md)** - Configuração de ambientes de homologação (`staging`) e produção (`production`), além de escopos OIDC.
- 🚪 **[Single Sign-Out (Logout)](logout.md)** - Como implementar e configurar o logout federado.
- 📚 **[Referência da API](api-reference.md)** - Detalhes e assinaturas das views, backend de autenticação e cliente HTTP.
- 📝 **[Histórico de Mudanças](changelog.md)** - Notas de versão e histórico de alterações do projeto.

