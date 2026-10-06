# Bulk Certificate Generator API

A FastAPI backend that accepts bulk certificate generation requests, processes recipients independently, tracks job progress, and provides generated certificates for retrieval.

## Current status

Phase 1: project foundation and health endpoint.

## Local setup

```bash
python -m venv .venv
# Windows PowerShell
.\.venv\Scripts\Activate.ps1

pip install -r requirements.txt
uvicorn app.main:app --reload
```

Open the API documentation at `http://127.0.0.1:8000/docs`.

## Tests

```bash
pytest
```

## Planned architecture

- FastAPI for the REST API
- PostgreSQL for jobs and recipient status
- SQLAlchemy for database access
- Pydantic for request/response validation
- ReportLab for PDF certificate generation
- FastAPI background processing for bulk generation
- Pytest for automated tests
