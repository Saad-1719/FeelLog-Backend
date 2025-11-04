
# FeelLog — Backend

A production-minded backend for a journaling and affirmations application. This repository demonstrates practical backend engineering skills: API design, authentication and authorization, data modelling, migrations, secure credential handling, and clear separation of concerns.

## At-a-glance

- Language: Python
- Approx. stack: FastAPI-like project layout, Pydantic (schemas), SQLAlchemy (ORM), Alembic (migrations), token-based auth utilities
- Primary responsibilities demonstrated: API design, user authentication, database schema management, utils for password/email/encryption

This project is suitable as a portfolio piece to showcase backend architecture, maintainability, and secure implementation patterns.

## Contents / Where to look

- `main.py` — Application entrypoint
- `requirements.txt` — Project dependencies
- `alembic/` — DB migrations and Alembic configuration

app/
- `app/api/routes/` — HTTP route handlers
  - `auth_routes.py` — signup, login, token/session endpoints
  - `journals_route.py` — CRUD endpoints for user journals
- `app/core/config.py` — config management (env variables)
- `app/dependencies/auth.py` — auth-related dependency providers (current user, security)
- `app/models/` — SQLAlchemy models (`auth.py`, `journals.py`)
- `app/schemas/` — Pydantic request/response schemas
- `app/services/db.py` — DB session / engine setup
- `app/utils/` — helper modules (passwords, tokens, encryption, email, affirmations)

Each folder follows a single responsibility principle: routes -> schemas -> models -> services -> utils.

## Features implemented

- User registration and authentication (secure password hashing + token handling)
- Journal creation, retrieval, update, and deletion
- Alembic-based DB migrations and version history
- Utility modules for email delivery, encryption helpers, and affirmation-specific logic

## Quick start (developer)

1. Create and activate a virtual environment

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

2. Provide environment variables (example names — verify `app/core/config.py` for exact names)

```bash
export DATABASE_URL="postgresql://user:pass@localhost:5432/feellog"
export SECRET_KEY="a-strong-secret"
# Optional (email): SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS
```

3. Run database migrations

```bash
alembic upgrade head
```

4. Start the application (example with Uvicorn)

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

By default, FastAPI-style apps expose interactive docs at `/docs` and `/redoc`. Confirm the API root in `main.py`.

## Environment & configuration

Check `app/core/config.py` for environment variable names and configuration defaults. Typical variables you will need:

- `DATABASE_URL` — SQLAlchemy connection string
- `SECRET_KEY` — cryptographic secret for token signing
- (Optional) SMTP configuration for email features

Store secrets securely (CI/CD secrets, `dotenv` in local development, or a secret manager for production).

## Architecture notes (short)

- Models (SQLAlchemy) are strictly separated from API schemas (Pydantic) to avoid leaking internal representations.
- Auth flows are encapsulated in utils and dependencies to make routes focused and testable.
- Database migrations are handled with Alembic; migration files are in `alembic/versions/` to show schema evolution.



Last updated: 2025-11-05


