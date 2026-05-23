# LeadForge Backend — Fase 4.1 (Backend Base)

Minimal FastAPI foundation for LeadForge-Agentic Core. This phase ships
**only** the backend skeleton:

- FastAPI app with CORS + lifespan
- Pydantic v2 schemas (Lead, Run, QA, Health) mirroring the frontend contract
- SQLite via SQLAlchemy 2.x (`create_all` on startup)
- `/health` endpoint with DB connectivity check
- Centralized config via `pydantic-settings` and `.env`
- Minimal stdlib logging

**Not in this phase:** agents, LangGraph, RAG, Chroma, Ollama, Groq, any LLM
calls, frontend wiring, authentication, deployment, real lead processing.

## Folder layout

```
backend/
├── app/
│   ├── main.py              FastAPI app factory + lifespan
│   ├── core/
│   │   ├── config.py        Pydantic Settings (.env)
│   │   └── logging.py       stdlib logging setup
│   ├── api/
│   │   ├── deps.py          shared dependencies (get_db)
│   │   └── routes/
│   │       └── health.py    GET /health
│   ├── schemas/             Pydantic v2 DTOs (contract for Block 4.2+)
│   │   ├── common.py
│   │   ├── lead.py
│   │   ├── qa.py
│   │   ├── run.py
│   │   └── health.py
│   ├── services/            (empty placeholder for Block 4.2+)
│   └── db/
│       ├── base.py          DeclarativeBase
│       ├── session.py       engine + SessionLocal
│       ├── models.py        Lead / Run / AgentTrace / QAResult tables
│       └── init_db.py       create_all()
├── tests/
│   └── test_health.py
├── requirements.txt
├── .env.example
└── .gitignore
```

## Quick start

From the repo root:

```bash
cd backend
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Then open:

- Health: <http://localhost:8000/health>
- OpenAPI docs: <http://localhost:8000/docs>

Expected `/health` response:

```json
{
  "status": "ok",
  "app": "leadforge-backend",
  "version": "0.1.0",
  "env": "development",
  "db": "ok"
}
```

## Tests

```bash
cd backend
pytest -q
```

## Environment variables

See `.env.example`. Only Fase 4.1 variables are active:

| Variable        | Default                          | Purpose                       |
|-----------------|----------------------------------|-------------------------------|
| `APP_NAME`      | `leadforge-backend`              | Reported by `/health`         |
| `APP_ENV`       | `development`                    | Reported by `/health`         |
| `APP_VERSION`   | `0.1.0`                          | Reported by `/health`         |
| `APP_HOST`      | `0.0.0.0`                        | Bind host (for `uvicorn`)     |
| `APP_PORT`      | `8000`                           | Bind port (for `uvicorn`)     |
| `LOG_LEVEL`     | `INFO`                           | Root logger level             |
| `DATABASE_URL`  | `sqlite:///./leadforge.db`       | SQLAlchemy connection URL     |
| `CORS_ORIGINS`  | `http://localhost:3000`          | Comma-separated allowed origins |
| `GROQ_API_KEY`  | (unset)                          | Optional Groq API key (not required for demo) |
| `GROQ_DEFAULT_MODEL` | `llama-3.1-8b-instant`      | Default Groq model when key is set |
| `GROQ_TIMEOUT_SECONDS` | `30`                      | Groq request timeout |

Optional Groq settings (`GROQ_API_KEY`, `GROQ_DEFAULT_MODEL`,
`GROQ_TIMEOUT_SECONDS`) are read when set; the app runs without them.
Other future-phase variables (cost caps, feature flags) in `.env.example`
are documented but not read yet.

## Notes

- No migration tool yet. Schema is created via `Base.metadata.create_all()`
  on app startup. Alembic will be introduced in a later phase if needed.
- ORM models exist (`Lead`, `Run`, `AgentTrace`, `QAResult`) but no
  endpoint reads or writes them yet. They define the persistence shape for
  Block 4.2+.
- The frontend (`app/`, `components/`, …) is **not** touched in this phase.
