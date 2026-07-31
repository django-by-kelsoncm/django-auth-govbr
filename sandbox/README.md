# Sandbox Django para django-auth-govbr

Aplicação Django de demonstração e testes manuais da biblioteca `django-auth-govbr`.

## Como executar

1. Copie o arquivo de exemplo de ambiente:
   ```bash
   cp .env.example .env
   ```
2. Configure suas credenciais do Gov.br no `.env`:
   - `GOVBR_CLIENT_ID`
   - `GOVBR_CLIENT_SECRET`
   - `GOVBR_REDIRECT_URI`
3. Execute as migrações e inicie o servidor local:
   ```bash
   python manage.py migrate
   python manage.py runserver
   ```
4. Acesse `http://localhost:8000` no navegador.
