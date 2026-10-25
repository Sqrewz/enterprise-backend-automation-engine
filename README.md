# Enterprise Backend & Automation Engine

Production-oriented FastAPI service that combines task management, business intelligence reporting, document processing, RAG knowledge retrieval, and secure webhook automation.

## Architecture

```text
API endpoints → Core (security/config/logging) → Services → Async SQLAlchemy → PostgreSQL
                                                     └──── Celery + Redis
```

| Domain | Included capability |
|---|---|
| Task & Workflow | JWT, Argon2 password hashing, RBAC, ownership, filtering, pagination, and configurable workflows |
| BI | Pandas analysis, ReportLab PDF generation, and a daily Celery Beat cron report |
| Document | PDF/DOCX/TXT validation, upload-size limits, and text/metadata extraction |
| RAG | Database-backed context retrieval and Google Gemini answer generation |
| Webhook | HMAC-SHA256 verification, idempotency keys, and asynchronous outbound notifications |

## Run with Docker

1. Copy `.env.example` to `.env` and replace the placeholder secrets.
2. Start the stack:

```bash
docker compose up --build
```

Swagger UI: `http://localhost:8000/docs`
Health check: `http://localhost:8000/health`

The stack includes the API, Celery worker, Celery Beat scheduler, PostgreSQL, and Redis. Upload and report directories are mounted to the host.

## Local development

```bash
python -m venv .venv
.venv\\Scripts\\activate
pip install -e ".[dev]"
copy .env.example .env
uvicorn app.main:app --reload
pytest
```

To start background workers locally:

```bash
celery -A app.workers.celery_app worker --loglevel=INFO
celery -A app.workers.celery_app beat --loglevel=INFO
```

## API quick start

1. Create a user with `POST /api/v1/auth/register`.
2. Sign in with `POST /api/v1/auth/login`, using OAuth2 form data (`username` is the email address).
3. Send `Authorization: Bearer <token>` with protected requests.
4. Use `/api/v1/tasks` for task management. Members can view only their own tasks. Admins and managers can create workflows through `/api/v1/workflows`.
5. Upload a document through `POST /api/v1/documents`, then ask questions with `POST /api/v1/knowledge/ask`.
6. Admins and managers can queue a PDF report through `POST /api/v1/reports`.

## Webhook security

Sign the raw request body with `HMAC-SHA256(WEBHOOK_SECRET, raw_body)` and place the hexadecimal digest in the `X-Signature` header. Every request requires a unique `Idempotency-Key`. Send requests to `POST /api/v1/webhooks/{event_type}`; duplicate keys are acknowledged but never processed again.

## Production notes

- Manage secrets with a secret manager, terminate TLS at the edge, restrict CORS, and run Alembic migrations as part of deployment.
- Add object storage and antivirus scanning before accepting untrusted documents at scale.
- Set `GEMINI_API_KEY` to enable Gemini; otherwise, the service returns a safe context fallback.
- Structured JSON logs are written to stdout for centralized log aggregation.
